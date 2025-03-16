from sqlalchemy import Column, String, Integer, Float, JSON, ForeignKey, DateTime, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database.config import Base
from .progress import progress_poi_association
import uuid
from typing import Dict, List, Optional

class POIContentConflict(Base):
    __tablename__ = "poi_content_conflicts"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    poi_id = Column(String, ForeignKey("points_of_interest.id"), nullable=False)
    base_version = Column(Integer, nullable=False)  # Version the changes were based on
    proposed_changes = Column(JSON, nullable=False)  # The actual content changes
    conflict_type = Column(String, nullable=False)  # Type of conflict (concurrent_edit, merge_conflict, etc)
    status = Column(String, nullable=False, default="pending")  # pending, resolved, rejected
    resolution_strategy = Column(String)  # How the conflict was/should be resolved
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True))
    resolved_by = Column(String)  # User who resolved the conflict
    conflict_metadata = Column(JSON)  # Additional metadata about the conflict
    
    # Relationship back to POI
    poi = relationship("PointOfInterest", back_populates="content_conflicts")

class PointOfInterest(Base):
    __tablename__ = "points_of_interest"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    region_id = Column(String, ForeignKey("regions.id"), nullable=False)
    name = Column(String, nullable=False)
    local_name = Column(String)
    location = Column(JSON, nullable=False)  # {lat: float, lon: float}
    type = Column(String, nullable=False)
    difficulty = Column(Integer, default=1)  # 1-5 scale
    content_version = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Content in multiple languages
    content = Column(JSON, nullable=False)  # {lang_code: {title, description, hints}}
    
    # Achievement criteria
    achievement_criteria = Column(JSON)  # {type: str, requirements: dict}
    points_value = Column(Integer, default=10)
    time_estimate = Column(Integer)  # estimated completion time in minutes
    
    # Learning objectives
    learning_objectives = Column(JSON)  # {vocabulary: [], grammar: [], cultural: []}
    
    # Metadata for offline sync
    sync_metadata = Column(JSON)  # {last_sync: timestamp, version: str}
    is_published = Column(Boolean, default=True)
    
    # Content history
    content_history = Column(JSON, default=lambda: [], nullable=False)
    
    # Relationships
    region = relationship("Region", back_populates="points_of_interest")
    progress_records = relationship(
        "UserProgress",
        secondary=progress_poi_association,
        back_populates="completed_pois"
    )
    
    # Add relationship to conflicts
    content_conflicts = relationship("POIContentConflict", back_populates="poi")
    
    def to_dict(self):
        """Convert POI to dictionary format"""
        return {
            "id": self.id,
            "region_id": self.region_id,
            "name": self.name,
            "local_name": self.local_name,
            "location": self.location,
            "type": self.type,
            "difficulty": self.difficulty,
            "content": self.content,
            "achievement_criteria": self.achievement_criteria,
            "points_value": self.points_value,
            "time_estimate": self.time_estimate,
            "learning_objectives": self.learning_objectives,
            "content_version": self.content_version,
            "is_published": self.is_published,
            "sync_metadata": self.sync_metadata,
            "content_history": self.content_history
        }
        
    def validate_completion(self, progress_data: dict) -> bool:
        """
        Validate if a user has completed this POI's requirements
        Args:
            progress_data: Dict containing user's progress data
        Returns:
            bool: Whether requirements are met
        """
        if not self.achievement_criteria:
            return True
            
        criteria = self.achievement_criteria
        if criteria["type"] == "visit":
            return True  # Just being there is enough
            
        elif criteria["type"] == "duration":
            min_duration = criteria["requirements"]["minutes"]
            actual_duration = progress_data.get("duration", 0)
            return actual_duration >= min_duration
            
        elif criteria["type"] == "interaction":
            required_interactions = criteria["requirements"]["count"]
            actual_interactions = len(progress_data.get("interactions", []))
            return actual_interactions >= required_interactions
            
        elif criteria["type"] == "quiz":
            required_score = criteria["requirements"]["min_score"]
            actual_score = progress_data.get("quiz_score", 0)
            return actual_score >= required_score
            
        return False

    def update_content_version(self, change_description: str = None, changed_by: str = None):
        """Increment content version and update sync metadata with history"""
        self.content_version += 1
        current_time = str(func.now())
        
        # Update sync metadata
        self.sync_metadata = {
            "last_sync": current_time,
            "version": str(self.content_version),
            "update_type": "content"
        }
        
        # Add to history
        history_entry = {
            "version": self.content_version,
            "timestamp": current_time,
            "change_description": change_description,
            "changed_by": changed_by
        }
        
        if not self.content_history:
            self.content_history = []
        self.content_history.append(history_entry)
    
    def validate_content_version(self, client_version: int) -> bool:
        """Check if client has latest content version"""
        return client_version == self.content_version
    
    def get_version_info(self) -> dict:
        """Get version information including sync status and history"""
        return {
            "current_version": self.content_version,
            "last_sync": self.sync_metadata.get("last_sync") if self.sync_metadata else None,
            "update_type": self.sync_metadata.get("update_type") if self.sync_metadata else None,
            "history": self.content_history
        }

    def get_content_diff(self, from_version: int) -> dict:
        """Get content changes between versions"""
        if not self.content_history:
            return {"changes": [], "from_version": from_version, "to_version": self.content_version}
            
        changes = [
            change for change in self.content_history 
            if change["version"] > from_version
        ]
        
        return {
            "changes": changes,
            "from_version": from_version,
            "to_version": self.content_version
        }
    
    def create_pending_change(self, changes: Dict, change_type: str = "update") -> POIContentConflict:
        """Create a pending content change that needs review"""
        conflict = POIContentConflict(
            poi_id=self.id,
            base_version=self.content_version,
            proposed_changes=changes,
            conflict_type="concurrent_edit" if self.has_pending_changes() else change_type,
            conflict_metadata={
                "previous_content": self.content,
                "timestamp": str(func.now())
            }
        )
        return conflict
    
    def has_pending_changes(self) -> bool:
        """Check if there are any pending changes for this POI"""
        return any(c.status == "pending" for c in self.content_conflicts)
    
    def get_pending_changes(self) -> List[POIContentConflict]:
        """Get all pending changes for this POI"""
        return [c for c in self.content_conflicts if c.status == "pending"]
    
    def rollback_to_version(self, target_version: int) -> bool:
        """Roll back content to a specific version"""
        if not self.content_history:
            return False
            
        # Find the target version in history
        target_state = None
        for entry in self.content_history:
            if entry["version"] == target_version:
                target_state = entry.get("content_snapshot")
                break
                
        if not target_state:
            return False
            
        # Create a pending change for the rollback
        self.create_pending_change(
            changes=target_state,
            change_type="rollback"
        )
        return True
    
    def resolve_conflict(self, conflict_id: str, resolution: Dict, resolved_by: str) -> bool:
        """Resolve a content conflict"""
        conflict = next((c for c in self.content_conflicts if c.id == conflict_id), None)
        if not conflict or conflict.status != "pending":
            return False
            
        strategy = resolution.get("strategy")
        if strategy == "accept":
            # Accept the proposed changes entirely
            self.content = conflict.proposed_changes
            self.update_content_version(
                change_description="Accepted proposed changes",
                changed_by=resolved_by
            )
        elif strategy == "reject":
            # Reject the changes, keep current content
            conflict.status = "rejected"
            conflict.resolved_at = func.now()
            conflict.resolved_by = resolved_by
            conflict.resolution_strategy = "reject"
            return True
        elif strategy == "merge":
            merge_strategy = resolution.get("merge_strategy", "manual")
            if merge_strategy == "manual" and "merged_content" in resolution:
                # Use manually merged content
                self.content = resolution["merged_content"]
            else:
                # Use automated merge strategy
                merged_content = self._merge_changes(
                    conflict.proposed_changes,
                    merge_strategy
                )
                self.content = merged_content
            
            self.update_content_version(
                change_description=f"Merged changes with {merge_strategy} strategy",
                changed_by=resolved_by
            )
        else:
            return False
            
        # Update conflict status
        conflict.status = "resolved"
        conflict.resolved_at = func.now()
        conflict.resolved_by = resolved_by
        conflict.resolution_strategy = strategy
        
        # Add resolution metadata
        if not conflict.conflict_metadata:
            conflict.conflict_metadata = {}
        conflict.conflict_metadata.update({
            "resolution_timestamp": str(func.now()),
            "resolution_method": strategy,
            "merge_strategy": resolution.get("merge_strategy"),
            "resolved_version": self.content_version
        })
        
        return True

    def _merge_changes(self, proposed_changes: Dict, strategy: str = "manual") -> Dict:
        """Merge proposed changes with current content"""
        if strategy == "manual":
            # Use the manually provided merged content
            return proposed_changes
        elif strategy == "take_newest":
            # Compare timestamps and take the newest changes
            current_timestamp = self.sync_metadata.get("last_sync")
            proposed_timestamp = proposed_changes.get("metadata", {}).get("timestamp")
            if not current_timestamp or not proposed_timestamp:
                return self.content  # Keep current if timestamps unavailable
            return proposed_changes if proposed_timestamp > current_timestamp else self.content
        elif strategy == "selective":
            # Merge only non-conflicting changes, keeping both versions where they differ
            merged = self.content.copy()
            for lang, content in proposed_changes.items():
                if lang not in merged:
                    # New language content
                    merged[lang] = content
                else:
                    # Existing language, merge non-conflicting fields
                    for field, value in content.items():
                        if field not in merged[lang] or merged[lang][field] == value:
                            merged[lang][field] = value
                        else:
                            # Conflict - keep both versions
                            if not isinstance(merged[lang][field], list):
                                merged[lang][field] = [merged[lang][field]]
                            if value not in merged[lang][field]:
                                merged[lang][field].append(value)
            return merged
        else:
            return self.content  # Unknown strategy, keep current content