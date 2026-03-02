import boto3
import json

bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')

# Test Claude
print("Testing Claude 3 Sonnet...")
try:
    response = bedrock.invoke_model(
        modelId='anthropic.claude-3-sonnet-20240229-v1:0',
        body=json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "messages": [{"role": "user", "content": "Hello"}],
            "max_tokens": 100
        })
    )
    result = json.loads(response['body'].read())
    print("✅ Claude 3 Sonnet: WORKING")
    print(f"Response: {result['content'][0]['text']}\n")
except Exception as e:
    print(f"❌ Claude 3 Sonnet: FAILED")
    print(f"Error: {e}\n")

# Test Titan Embeddings
print("Testing Titan Embeddings...")
try:
    response = bedrock.invoke_model(
        modelId='amazon.titan-embed-text-v1',
        body=json.dumps({"inputText": "test"})
    )
    result = json.loads(response['body'].read())
    print("✅ Titan Embeddings: WORKING")
    print(f"Embedding dimensions: {len(result['embedding'])}\n")
except Exception as e:
    print(f"❌ Titan Embeddings: FAILED")
    print(f"Error: {e}\n")
