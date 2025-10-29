'''
[notice] To update, run: C:\Users\jayanth\AppData\Local\Programs\Python\Python312\python.exe -m pip install --upgrade pip
Creating layer zip file...
Detected OS: windows
Source (Windows path): C:\Users\jayanth\AppData\Local\Temp\lambda_deploy_201_15332\python
Destination (Windows path): C:\Users\jayanth\AppData\Local\Temp\lambda_deploy_201_15332\layer.zip
✅ Layer zip created successfully: /tmp/lambda_deploy_201_15332/layer.zip
Layer zip size: 17M
AWS CLI path: C:/Users/jayanth/AppData/Local/Temp/lambda_deploy_201_15332/layer.zip
Publishing Lambda layer...
Layer Version ARN: arn:aws:lambda:us-east-1:058264125602:layer:aegis-python-dependencies:1

Lambda Role ARN: arn:aws:iam::058264125602:role/lambda-bedrock-role

📦 Step 3: Packaging and Deploying Lambda Functions...   

Deploying aegis-payment-tools (payment_tools.py)...      
----------------------------------------
Source file (Windows path): C:\Users\jayanth\AppData\Local\Temp\lambda_deploy_201_24999\lambda_function.py        
Destination (Windows path): C:\Users\jayanth\AppData\Local\Temp\lambda_deploy_201_24999\function.zip
✅ Function zip created: 4.0K
AWS CLI path: C:/Users/jayanth/AppData/Local/Temp/lambda_deploy_201_24999/function.zip
Creating new function...
{
    "FunctionName": "aegis-payment-tools",
    "FunctionArn": "arn:aws:lambda:us-east-1:058264125602:function:aegis-payment-tools",
    "Runtime": "python3.11",
    "Role": "arn:aws:iam::058264125602:role/lambda-bedrock-role",
    "Handler": "lambda_function.lambda_handler",        
    "CodeSize": 1476,
    "Description": "",
    "Timeout": 60,
    "MemorySize": 512,
    "LastModified": "2025-10-17T06:56:30.922+0000",     
    "CodeSha256": "8UMp5eBObDRPVIi1/MLBqWhdd7bW/zL68w6v66PIMJY=",
    "Version": "$LATEST",
    "TracingConfig": {
        "Mode": "PassThrough"
    },
    "RevisionId": "10999cbf-bb12-4f51-ba51-9ef4947d3dd8",    "Layers": [
        {
            "Arn": "arn:aws:lambda:us-east-1:058264125602:layer:aegis-python-dependencies:1",
            "CodeSize": 16811164
        }
    ],
    "State": "Pending",
    "StateReason": "The function is being created.",    
    "StateReasonCode": "Creating",
    "PackageType": "Zip",
    "Architectures": [
        "x86_64"
    ],
    "EphemeralStorage": {
        "Size": 512
    },
    "SnapStart": {
        "ApplyOn": "None",
        "OptimizationStatus": "Off"
    },
    "RuntimeVersionConfig": {
        "RuntimeVersionArn": "arn:aws:lambda:us-east-1::runtime:6c687d1ae05d783a82cd99c5896c1baddfe1daf7ac4068082fb989401de8b287"
    },
    "LoggingConfig": {
        "LogFormat": "Text",
        "LogGroup": "/aws/lambda/aegis-payment-tools"   
    }
}

Waiting for function to be active...
✅ aegis-payment-tools deployed successfully

Deploying aegis-verification-tools (verification_tools.py)...
----------------------------------------
Source file (Windows path): C:\Users\jayanth\AppData\Local\Temp\lambda_deploy_201_1073\lambda_function.py
Destination (Windows path): C:\Users\jayanth\AppData\Local\Temp\lambda_deploy_201_1073\function.zip
✅ Function zip created: 4.0K
AWS CLI path: C:/Users/jayanth/AppData/Local/Temp/lambda_deploy_201_1073/function.zip
Creating new function...
{
    "FunctionName": "aegis-verification-tools",
    "FunctionArn": "arn:aws:lambda:us-east-1:058264125602:function:aegis-verification-tools",
    "Runtime": "python3.11",
    "Role": "arn:aws:iam::058264125602:role/lambda-bedrock-role",
    "Handler": "lambda_function.lambda_handler",
    "CodeSize": 978,
    "Description": "",
    "Timeout": 60,
    "MemorySize": 512,
    "LastModified": "2025-10-17T06:56:55.733+0000",      
    "CodeSha256": "3SzfJWEa3J9INp3TetthjrH4u4YjApWR221JY43TVlk=",
    "Version": "$LATEST",
    "TracingConfig": {
        "Mode": "PassThrough"
    },
    "RevisionId": "6a58c9e2-8de8-41c4-a7d2-0ad7cc837d9d",    "Layers": [
        {
            "Arn": "arn:aws:lambda:us-east-1:058264125602:layer:aegis-python-dependencies:1",
            "CodeSize": 16811164
        }
    ],
    "State": "Pending",
    "StateReason": "The function is being created.",    
    "StateReasonCode": "Creating",
    "PackageType": "Zip",
    "Architectures": [
        "x86_64"
    ],
    "EphemeralStorage": {
        "Size": 512
    },
    "SnapStart": {
        "ApplyOn": "None",
        "OptimizationStatus": "Off"
    },
    "RuntimeVersionConfig": {
        "RuntimeVersionArn": "arn:aws:lambda:us-east-1::runtime:6c687d1ae05d783a82cd99c5896c1baddfe1daf7ac4068082fb989401de8b287"
    },
    "LoggingConfig": {
        "LogFormat": "Text",
        "LogGroup": "/aws/lambda/aegis-verification-tools"
    }
}

Waiting for function to be active...
✅ aegis-verification-tools deployed successfully

Deploying aegis-customer-tools (customer_tools.py)...
----------------------------------------
Source file (Windows path): C:\Users\jayanth\AppData\Local\Temp\lambda_deploy_201_10629\lambda_function.py        
Destination (Windows path): C:\Users\jayanth\AppData\Local\Temp\lambda_deploy_201_10629\function.zip
✅ Function zip created: 4.0K
AWS CLI path: C:/Users/jayanth/AppData/Local/Temp/lambda_deploy_201_10629/function.zip
Creating new function...
{
    "FunctionName": "aegis-customer-tools",
    "FunctionArn": "arn:aws:lambda:us-east-1:058264125602:function:aegis-customer-tools",
    "Runtime": "python3.11",
    "Role": "arn:aws:iam::058264125602:role/lambda-bedrock-role",
    "Handler": "lambda_function.lambda_handler",        
    "CodeSize": 904,
    "Description": "",
    "Timeout": 60,
    "MemorySize": 512,
    "LastModified": "2025-10-17T06:57:33.452+0000",     
    "CodeSha256": "T0JE2KEamT9AcAGfmfrwOBrj6ab9Wx7UdxK2Yjy1dfk=",
    "Version": "$LATEST",
    "TracingConfig": {
        "Mode": "PassThrough"
    },
    "RevisionId": "a19d6aa2-b921-457e-8165-0339a1f135be",    "Layers": [
        {
            "Arn": "arn:aws:lambda:us-east-1:058264125602:layer:aegis-python-dependencies:1",
            "CodeSize": 16811164
        }
    ],
    "State": "Pending",
    "StateReason": "The function is being created.",    
    "StateReasonCode": "Creating",
    "PackageType": "Zip",
    "Architectures": [
        "x86_64"
    ],
    "EphemeralStorage": {
        "Size": 512
    },
    "SnapStart": {
        "ApplyOn": "None",
        "OptimizationStatus": "Off"
    },
    "RuntimeVersionConfig": {
        "RuntimeVersionArn": "arn:aws:lambda:us-east-1::runtime:6c687d1ae05d783a82cd99c5896c1baddfe1daf7ac4068082fb989401de8b287"
    },
    "LoggingConfig": {
        "LogFormat": "Text",
        "LogGroup": "/aws/lambda/aegis-customer-tools"  
    }
}

Waiting for function to be active...
✅ aegis-customer-tools deployed successfully

Deploying aegis-graph-tools (graph_tools.py)...
----------------------------------------
Source file (Windows path): C:\Users\jayanth\AppData\Local\Temp\lambda_deploy_201_21012\lambda_function.py        
Destination (Windows path): C:\Users\jayanth\AppData\Local\Temp\lambda_deploy_201_21012\function.zip
✅ Function zip created: 1.0K
AWS CLI path: C:/Users/jayanth/AppData/Local/Temp/lambda_deploy_201_21012/function.zip
Creating new function...
{
    "FunctionName": "aegis-graph-tools",
    "FunctionArn": "arn:aws:lambda:us-east-1:058264125602:function:aegis-graph-tools",
    "Runtime": "python3.11",
    "Role": "arn:aws:iam::058264125602:role/lambda-bedrock-role",
    "Handler": "lambda_function.lambda_handler",
    "CodeSize": 698,
    "Description": "",
    "Timeout": 60,
    "MemorySize": 512,
    "LastModified": "2025-10-17T06:58:07.629+0000",      
    "CodeSha256": "01N+ToccAU4NYrFAqdjsQYIz1cpMeUH+cmGzcHF9PrY=",
    "Version": "$LATEST",
    "TracingConfig": {
        "Mode": "PassThrough"
    },
    "RevisionId": "f6b645d5-17c3-4c0b-9872-65d4b98f215c",    "Layers": [
        {
            "Arn": "arn:aws:lambda:us-east-1:058264125602:layer:aegis-python-dependencies:1",
            "CodeSize": 16811164
        }
    ],
    "State": "Pending",
    "StateReason": "The function is being created.",    
    "StateReasonCode": "Creating",
    "PackageType": "Zip",
    "Architectures": [
        "x86_64"
    ],
    "EphemeralStorage": {
        "Size": 512
    },
    "SnapStart": {
        "ApplyOn": "None",
        "OptimizationStatus": "Off"
    },
    "RuntimeVersionConfig": {
        "RuntimeVersionArn": "arn:aws:lambda:us-east-1::runtime:6c687d1ae05d783a82cd99c5896c1baddfe1daf7ac4068082fb989401de8b287"
    },
    "LoggingConfig": {
        "LogFormat": "Text",
        "LogGroup": "/aws/lambda/aegis-graph-tools"     
    }
}

Waiting for function to be active...
✅ aegis-graph-tools deployed successfully

Deploying aegis-ml-tools (ml_model_tools.py)...
----------------------------------------
Source file (Windows path): C:\Users\jayanth\AppData\Local\Temp\lambda_deploy_201_5259\lambda_function.py
Destination (Windows path): C:\Users\jayanth\AppData\Local\Temp\lambda_deploy_201_5259\function.zip
✅ Function zip created: 4.0K
AWS CLI path: C:/Users/jayanth/AppData/Local/Temp/lambda_deploy_201_5259/function.zip
Creating new function...
{
    "FunctionName": "aegis-ml-tools",
    "FunctionArn": "arn:aws:lambda:us-east-1:058264125602:function:aegis-ml-tools",
    "Runtime": "python3.11",
    "Role": "arn:aws:iam::058264125602:role/lambda-bedrock-role",
    "Handler": "lambda_function.lambda_handler",
    "CodeSize": 1505,
    "Description": "",
    "Timeout": 60,
    "MemorySize": 512,
    "LastModified": "2025-10-17T06:58:50.413+0000",     
    "CodeSha256": "rXLUt+7qysMv6H4pJIc65xQND3zHZNIsdXcNr0hV5Hs=",
    "Version": "$LATEST",
    "TracingConfig": {
        "Mode": "PassThrough"
    },
    "RevisionId": "11e5f594-2348-451e-8253-c2a4e5ff1651",    "Layers": [
        {
            "Arn": "arn:aws:lambda:us-east-1:058264125602:layer:aegis-python-dependencies:1",
            "CodeSize": 16811164
        }
    ],
    "State": "Pending",
    "StateReason": "The function is being created.",    
    "StateReasonCode": "Creating",
    "PackageType": "Zip",
    "Architectures": [
        "x86_64"
    ],
    "EphemeralStorage": {
        "Size": 512
    },
    "SnapStart": {
        "ApplyOn": "None",
        "OptimizationStatus": "Off"
    },
    "RuntimeVersionConfig": {
        "RuntimeVersionArn": "arn:aws:lambda:us-east-1::runtime:6c687d1ae05d783a82cd99c5896c1baddfe1daf7ac4068082fb989401de8b287"
    },
    "LoggingConfig": {
        "LogFormat": "Text",
        "LogGroup": "/aws/lambda/aegis-ml-tools"        
    }
}

Waiting for function to be active...
✅ aegis-ml-tools deployed successfully

Deploying aegis-kb-tools (knowledge_base_tools.py)...
----------------------------------------
Source file (Windows path): C:\Users\jayanth\AppData\Local\Temp\lambda_deploy_201_5745\lambda_function.py
Destination (Windows path): C:\Users\jayanth\AppData\Local\Temp\lambda_deploy_201_5745\function.zip
✅ Function zip created: 4.0K
AWS CLI path: C:/Users/jayanth/AppData/Local/Temp/lambda_deploy_201_5745/function.zip
Creating new function...
{
    "FunctionName": "aegis-kb-tools",
    "FunctionArn": "arn:aws:lambda:us-east-1:058264125602:function:aegis-kb-tools",
    "Runtime": "python3.11",
    "Role": "arn:aws:iam::058264125602:role/lambda-bedrock-role",
    "Handler": "lambda_function.lambda_handler",
    "CodeSize": 761,
    "Description": "",
    "Timeout": 60,
    "MemorySize": 512,
    "LastModified": "2025-10-17T06:59:17.025+0000",      
    "CodeSha256": "Lb9l0LCqiKgK9jc+qvwCvQvMrU1FupN5ZGogyoMQs44=",
    "Version": "$LATEST",
    "TracingConfig": {
        "Mode": "PassThrough"
    },
    "RevisionId": "787cc55c-fa0f-4f0e-a0be-87059114b7d4",    "Layers": [
        {
            "Arn": "arn:aws:lambda:us-east-1:058264125602:layer:aegis-python-dependencies:1",
            "CodeSize": 16811164
        }
    ],
    "State": "Pending",
    "StateReason": "The function is being created.",     
    "StateReasonCode": "Creating",
    "PackageType": "Zip",
    "Architectures": [
        "x86_64"
    ],
    "EphemeralStorage": {
        "Size": 512
    },
    "SnapStart": {
        "ApplyOn": "None",
        "OptimizationStatus": "Off"
    },
    "RuntimeVersionConfig": {
        "RuntimeVersionArn": "arn:aws:lambda:us-east-1::runtime:6c687d1ae05d783a82cd99c5896c1baddfe1daf7ac4068082fb989401de8b287"
    },
    "LoggingConfig": {
        "LogFormat": "Text",
        "LogGroup": "/aws/lambda/aegis-kb-tools"        
    }
}

Waiting for function to be active...
✅ aegis-kb-tools deployed successfully

Deploying aegis-case-tools (case_management_tools.py)...
----------------------------------------
Source file (Windows path): C:\Users\jayanth\AppData\Local\Temp\lambda_deploy_201_18715\lambda_function.py        
Destination (Windows path): C:\Users\jayanth\AppData\Local\Temp\lambda_deploy_201_18715\function.zip
✅ Function zip created: 4.0K
AWS CLI path: C:/Users/jayanth/AppData/Local/Temp/lambda_deploy_201_18715/function.zip
Creating new function...
{
    "FunctionName": "aegis-case-tools",
    "FunctionArn": "arn:aws:lambda:us-east-1:058264125602:function:aegis-case-tools",
    "Runtime": "python3.11",
    "Role": "arn:aws:iam::058264125602:role/lambda-bedrock-role",
    "Handler": "lambda_function.lambda_handler",
    "CodeSize": 1124,
    "Description": "",
    "Timeout": 60,
    "MemorySize": 512,
    "LastModified": "2025-10-17T06:59:38.781+0000",      
    "CodeSha256": "zz/NjUtH8qGJk+F5E3YQ8TwLxGFrAVBNaUcDmsxnnZs=",
    "Version": "$LATEST",
    "TracingConfig": {
        "Mode": "PassThrough"
    },
    "RevisionId": "2d7de2c0-d94d-4b73-8e10-5efd6581901e",    "Layers": [
        {
            "Arn": "arn:aws:lambda:us-east-1:058264125602:layer:aegis-python-dependencies:1",
            "CodeSize": 16811164
        }
    ],
    "State": "Pending",
    "StateReason": "The function is being created.",    
    "StateReasonCode": "Creating",
    "PackageType": "Zip",
    "Architectures": [
        "x86_64"
    ],
    "EphemeralStorage": {
        "Size": 512
    },
    "SnapStart": {
        "ApplyOn": "None",
        "OptimizationStatus": "Off"
    },
    "RuntimeVersionConfig": {
        "RuntimeVersionArn": "arn:aws:lambda:us-east-1::runtime:6c687d1ae05d783a82cd99c5896c1baddfe1daf7ac4068082fb989401de8b287"
    },
    "LoggingConfig": {
        "LogFormat": "Text",
        "LogGroup": "/aws/lambda/aegis-case-tools"      
    }
}

Waiting for function to be active...
✅ aegis-case-tools deployed successfully

============================================
✅ Lambda Functions Deployment Complete!
============================================

Deployed Functions:
  - aegis-payment-tools
  - aegis-verification-tools
  - aegis-customer-tools
  - aegis-graph-tools
  - aegis-ml-tools
  - aegis-kb-tools
  - aegis-case-tools

Next Steps:
  1. Configure AgentCore Gateway to use these Lambda ARNs
  2. Update agentcore.yaml with Lambda function ARNs     
  3. Deploy AgentCore Runtime with: bash deploy_agentcore.sh
'''


#!/bin/bash

###############################################################################
# Deploy Lambda Functions for AgentCore Gateway Tools
# 
# This script packages and deploys all Lambda functions used by AgentCore
# Gateway for the Aegis fraud prevention platform.
# Cross-platform compatible (Windows Git Bash, Linux, macOS)
###############################################################################

set -e

echo "🚀 Starting Lambda Functions Deployment..."
echo "============================================"

# Configuration
AWS_REGION=${AWS_REGION:-us-east-1}
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
LAMBDA_ROLE_NAME="lambda-bedrock-role"
LAMBDA_LAYER_NAME="aegis-python-dependencies"

echo "AWS Account ID: $ACCOUNT_ID"
echo "AWS Region: $AWS_REGION"
echo ""

###############################################################################
# Helper Functions for Cross-Platform Compatibility
###############################################################################

# Detect OS
detect_os() {
    case "$(uname -s)" in
        MINGW*|MSYS*|CYGWIN*)
            echo "windows"
            ;;
        Linux*)
            echo "linux"
            ;;
        Darwin*)
            echo "mac"
            ;;
        *)
            echo "unknown"
            ;;
    esac
}

# Convert Unix path to Windows path for PowerShell and AWS CLI
convert_path_for_windows() {
    local path=$1
    if command -v cygpath &> /dev/null; then
        cygpath -w "$path"
    else
        echo "$path"
    fi
}

# Get path for AWS CLI fileb:// parameter
get_aws_file_path() {
    local path=$1
    local os_type=$(detect_os)
    
    if [ "$os_type" == "windows" ]; then
        # Convert to Windows path and ensure forward slashes for AWS CLI
        if command -v cygpath &> /dev/null; then
            # Get Windows path and convert backslashes to forward slashes
            local win_path=$(cygpath -w "$path")
            echo "$win_path" | sed 's/\\/\//g'
        else
            echo "$path"
        fi
    else
        echo "$path"
    fi
}

# Cross-platform zip function for directories
create_zip_from_directory() {
    local source_dir=$1
    local zip_file=$2
    local os_type=$(detect_os)
    
    echo "Detected OS: $os_type"
    
    if [ "$os_type" == "windows" ]; then
        # Use PowerShell on Windows - convert paths first
        local win_source=$(convert_path_for_windows "$source_dir")
        local win_zip=$(convert_path_for_windows "$zip_file")
        
        echo "Source (Windows path): $win_source"
        echo "Destination (Windows path): $win_zip"
        
        # PowerShell command to zip directory contents
        powershell.exe -Command "\$ProgressPreference = 'SilentlyContinue'; Compress-Archive -Path '$win_source\\*' -DestinationPath '$win_zip' -Force"
    else
        # Use zip command on Linux/Mac
        echo "Using zip command..."
        cd "$(dirname "$source_dir")"
        zip -r "$zip_file" "$(basename "$source_dir")/"
        cd - > /dev/null
    fi
}

# Cross-platform zip function for single file
create_zip_from_file() {
    local source_file=$1
    local zip_file=$2
    local os_type=$(detect_os)
    
    if [ "$os_type" == "windows" ]; then
        # Use PowerShell on Windows - convert paths first
        local win_source=$(convert_path_for_windows "$source_file")
        local win_zip=$(convert_path_for_windows "$zip_file")
        
        echo "Source file (Windows path): $win_source"
        echo "Destination (Windows path): $win_zip"
        
        # PowerShell command to zip single file
        powershell.exe -Command "\$ProgressPreference = 'SilentlyContinue'; Compress-Archive -Path '$win_source' -DestinationPath '$win_zip' -Force"
    else
        # Use zip command on Linux/Mac
        cd "$(dirname "$source_file")"
        zip "$zip_file" "$(basename "$source_file")"
        cd - > /dev/null
    fi
}

# Cross-platform temporary directory creation
create_temp_dir() {
    local os_type=$(detect_os)
    
    if [ "$os_type" == "windows" ]; then
        # Use TEMP directory on Windows
        local temp_base="${TEMP:-/tmp}"
        local temp_dir="$temp_base/lambda_deploy_$$_$RANDOM"
        mkdir -p "$temp_dir"
        echo "$temp_dir"
    else
        # Use mktemp on Linux/Mac
        mktemp -d
    fi
}

###############################################################################
# Step 1: Create Lambda Layer for Dependencies
###############################################################################

echo "📦 Step 1: Creating Lambda Layer for Python Dependencies..."

# Create temp directory for layer
LAYER_DIR=$(create_temp_dir)
mkdir -p "$LAYER_DIR/python"

echo "Layer directory: $LAYER_DIR"

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --target "$LAYER_DIR/python" \
    boto3 \
    botocore \
    requests \
    python-dateutil

# Create layer zip
echo "Creating layer zip file..."
LAYER_ZIP="$LAYER_DIR/layer.zip"

create_zip_from_directory "$LAYER_DIR/python" "$LAYER_ZIP"

# Verify zip file was created
if [ ! -f "$LAYER_ZIP" ]; then
    echo "❌ Error: Failed to create layer.zip"
    exit 1
fi

echo "✅ Layer zip created successfully: $LAYER_ZIP"
echo "Layer zip size: $(du -h "$LAYER_ZIP" 2>/dev/null | cut -f1 || echo 'unknown')"

# Get the proper path for AWS CLI
AWS_LAYER_ZIP=$(get_aws_file_path "$LAYER_ZIP")
echo "AWS CLI path: $AWS_LAYER_ZIP"

# Publish layer
echo "Publishing Lambda layer..."
LAYER_VERSION_ARN=$(aws lambda publish-layer-version \
    --layer-name $LAMBDA_LAYER_NAME \
    --description "Python dependencies for Aegis Lambda functions" \
    --zip-file "fileb://$AWS_LAYER_ZIP" \
    --compatible-runtimes python3.11 python3.12 \
    --region $AWS_REGION \
    --query LayerVersionArn \
    --output text)

echo "Layer Version ARN: $LAYER_VERSION_ARN"
echo ""

# Cleanup
rm -rf "$LAYER_DIR"

###############################################################################
# Step 2: Get Lambda Role ARN
###############################################################################

LAMBDA_ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${LAMBDA_ROLE_NAME}"
echo "Lambda Role ARN: $LAMBDA_ROLE_ARN"
echo ""

###############################################################################
# Step 3: Package and Deploy Lambda Functions
###############################################################################

echo "📦 Step 3: Packaging and Deploying Lambda Functions..."

# Array of Lambda functions to deploy
declare -a LAMBDA_FUNCTIONS=(
    "payment_tools:aegis-payment-tools"
    "verification_tools:aegis-verification-tools"
    "customer_tools:aegis-customer-tools"
    "graph_tools:aegis-graph-tools"
    "ml_model_tools:aegis-ml-tools"
    "knowledge_base_tools:aegis-kb-tools"
    "case_management_tools:aegis-case-tools"
)

for FUNC in "${LAMBDA_FUNCTIONS[@]}"; do
    IFS=':' read -r FILE_NAME FUNCTION_NAME <<< "$FUNC"
    
    echo ""
    echo "Deploying $FUNCTION_NAME ($FILE_NAME.py)..."
    echo "----------------------------------------"
    
    # Create temp directory for function
    FUNC_DIR=$(create_temp_dir)
    
    # Copy function code
    cp "backend/tools/$FILE_NAME.py" "$FUNC_DIR/lambda_function.py"
    
    # Create zip file
    FUNC_ZIP="$FUNC_DIR/function.zip"
    
    create_zip_from_file "$FUNC_DIR/lambda_function.py" "$FUNC_ZIP"
    
    # Verify zip file was created
    if [ ! -f "$FUNC_ZIP" ]; then
        echo "❌ Error: Failed to create function.zip for $FUNCTION_NAME"
        rm -rf "$FUNC_DIR"
        continue
    fi
    
    echo "✅ Function zip created: $(du -h "$FUNC_ZIP" 2>/dev/null | cut -f1 || echo 'unknown')"
    
    # Get the proper path for AWS CLI
    AWS_FUNC_ZIP=$(get_aws_file_path "$FUNC_ZIP")
    echo "AWS CLI path: $AWS_FUNC_ZIP"
    
    # Create or update Lambda function
    if aws lambda get-function --function-name $FUNCTION_NAME --region $AWS_REGION 2>/dev/null; then
        echo "Updating existing function..."
        aws lambda update-function-code \
            --function-name $FUNCTION_NAME \
            --zip-file "fileb://$AWS_FUNC_ZIP" \
            --region $AWS_REGION
        
        # Wait for update to complete
        echo "Waiting for function update to complete..."
        aws lambda wait function-updated \
            --function-name $FUNCTION_NAME \
            --region $AWS_REGION 2>/dev/null || echo "Wait command not available, continuing..."
    else
        echo "Creating new function..."
        aws lambda create-function \
            --function-name $FUNCTION_NAME \
            --runtime python3.11 \
            --role $LAMBDA_ROLE_ARN \
            --handler lambda_function.lambda_handler \
            --zip-file "fileb://$AWS_FUNC_ZIP" \
            --timeout 60 \
            --memory-size 512 \
            --layers $LAYER_VERSION_ARN \
            --region $AWS_REGION
        
        # Wait for function to be active
        echo "Waiting for function to be active..."
        aws lambda wait function-active \
            --function-name $FUNCTION_NAME \
            --region $AWS_REGION 2>/dev/null || echo "Wait command not available, continuing..."
    fi
    
    echo "✅ $FUNCTION_NAME deployed successfully"
    
    # Cleanup
    rm -rf "$FUNC_DIR"
done

echo ""
echo "============================================"
echo "✅ Lambda Functions Deployment Complete!"
echo "============================================"
echo ""
echo "Deployed Functions:"
for FUNC in "${LAMBDA_FUNCTIONS[@]}"; do
    IFS=':' read -r FILE_NAME FUNCTION_NAME <<< "$FUNC"
    echo "  - $FUNCTION_NAME"
done

echo ""
echo "Next Steps:"
echo "  1. Configure AgentCore Gateway to use these Lambda ARNs"
echo "  2. Update agentcore.yaml with Lambda function ARNs"
echo "  3. Deploy AgentCore Runtime with: bash deploy_agentcore.sh"
echo ""




