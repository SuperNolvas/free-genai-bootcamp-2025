### LLM Prompt 

## Vocab Importer

### Business Goal: 
The prototype of the language learning app is built, but we need to quickly populate the application with word and word groups so students can begin testing the system.

There is currently no interface for manually adding words or words groups and the process would be too tedious. 

### You have been asked to:
create an internal facing tool to generate vocab 
Be able to export the generated vocab to json for later import
Be able  to import to import json files

### Technical Restrictions
Since this is an internal facing tool the fractional CTO wants you to use an app prototyping framework of your choice:
Gradio
Streamlit
FastHTML

You need to use an LLM in order to generate the target words and word groups.
You can use either an:
Managed/Serverless LLM API
Local LLM serving the model via OPEA

Make a vocabulary importer based on the above requirements where we have a text field that allows us to import a thematic category for the generation of language vocabulary.

When submitting that text field it should access an api endpoint (api route in app router) to invoke an LLM chat completion to an LLM on the server side (so provide a way to add a secret api key for the chosen LLM that won't be exposed in the codebase) and then pass that information back to the front end.

It has to create a structured JSON output like this example:

```JSON
{
  "vocabulary": [
    {
      "russian": "привет",
      "english": "hello",
      "partOfSpeech": "interjection",
      "category": "greetings"
    },
    {
      "russian": "спасибо",
      "english": "thank you",
      "partOfSpeech": "interjection",
      "category": "courtesy"
    },
    {
      "russian": "вода",
      "english": "water",
      "partOfSpeech": "noun",
      "category": "basic_needs"
    },
    {
      "russian": "хлеб",
      "english": "bread",
      "partOfSpeech": "noun",
      "category": "food"
    },
    {
      "russian": "книга",
      "english": "book",
      "partOfSpeech": "noun",
      "category": "objects"
    },
    {
      "russian": "идти",
      "english": "to go",
      "partOfSpeech": "verb",
      "category": "actions"
    },
    {
      "russian": "хороший",
      "english": "good",
      "partOfSpeech": "adjective",
      "category": "descriptions"
    },
    {
      "russian": "большой",
      "english": "big",
      "partOfSpeech": "adjective",
      "category": "descriptions"
    },
    {
      "russian": "да",
      "english": "yes",
      "partOfSpeech": "particle",
      "category": "basic_phrases"
    },
    {
      "russian": "нет",
      "english": "no",
      "partOfSpeech": "particle",
      "category": "basic_phrases"
    }
  ]
}
```
The JSON that is outputted back to the front end should be copyable so it should be sent to an input field and there should be a copy button so that it can be copied to the clipboard and that should give an alert that it was copied to the user's clipboard.

### Framework creation service

Bolt.new is a browser-based AI tool that lets users build web and mobile apps without writing code. It was developed by the StackBlitz team

https://bolt.new/

