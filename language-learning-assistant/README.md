# Language Learning Assistant

A web based language learning application with the ability to take transcriptions from YouTube and process them via Amazon Bedrock

### Install Prerequisites

Setup Amazon Bedrock

* Create AWS Account
* Create an IAM User
* Add Bedrock Access Policy and Inline policy for model access 

https://docs.aws.amazon.com/bedrock/latest/userguide/getting-started-api.html

* Enable LLM model access via Amazon Bedrock management console in AWS
* Create AccessID and AccessKey envars to enable boto3 access to models

https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html


### Running Frontend

```sh
streamlit run frontend/main.py
```

### Running Backend

```sh
cd backend
pip install -r requirements.txt
python backend/main.py
```

