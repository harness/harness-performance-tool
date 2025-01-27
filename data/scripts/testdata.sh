

# inputs

url=http://<ip> # https://12.1.2.31
username=<username> # harness username
password=<password> # harness user password
repoUserIds=("<userId1>" "<userId2>") # repo user id
repoTokens=("<token1>" "<token2>") # repo user token - https://github.com/settings/tokens
repoUrl=<repoUrl> # https://github.com/../repoName
repoBranchName=<branchName> # main
k8sNamespace=<namespace> # default
organizationCount=<count> # 5
projectCount=<count> # 2 (per organization)


### ------ cd input variables BEGIN ------ 
# k8s manifest details
manifestRepoUrl=<manifestRepoUrl>
manifestRepoCommitId=<manifestRepoCommitId>

# ecr artifact details
awsRegion=<awsRegion>
awsArtifactImage=<awsArtifactImage>
awsArtifactTag=<awsArtifactTag>

# secrets
awsaccesskey=<awsaccesskey>
awssecretkey=<awssecretkey>

### ------ cd input variables END ------ 


# login

b64Str=$(printf "%s" "$username:$password" | base64)
LOGIN_RESULT=$(curl --location "$url/gateway/api/users/login" \
--header 'content-type: application/json' \
--data "{\"authorization\":\"Basic $b64Str\"}")

accountId=(`echo ${LOGIN_RESULT} | grep -o '"defaultAccountId":"[^"]*' | cut -d : -f2 | cut -d "\"" -f2`)
token=(`echo ${LOGIN_RESULT} | grep -o '"token":"[^"]*' | cut -d : -f2 | cut -d "\"" -f2`)


# add github repository user id as harness secret
for index in "${!repoUserIds[@]}"; do
    userId="${repoUserIds[$index]}"
    response=$(curl --location "$url/gateway/ng/api/v2/secrets?routingId=$accountId&accountIdentifier=$accountId" \
    --header "Authorization: Bearer $token" \
    --header "content-type: application/json" \
    --data '{
        "secret": {
            "type": "SecretText",
            "name": "user'$index'",
            "identifier": "user'$index'",
            "description": "",
            "tags": {},
            "spec": {
                "value": "'$userId'",
                "secretManagerIdentifier": "harnessSecretManager",
                "valueType": "Inline"
            }
        }
    }')
 
    echo "\\n#adding github repository userid as harness secret : user$index"
    echo "$response\\n"
done
 
 
 
# add github repository token as harness secret
for index in "${!repoTokens[@]}"; do
    repoToken="${repoTokens[$index]}"
    response=$(curl --location "$url/gateway/ng/api/v2/secrets?routingId=$accountId&accountIdentifier=$accountId" \
    --header "Authorization: Bearer $token" \
    --header "content-type: application/json" \
    --data '{
        "secret": {
            "type": "SecretText",
            "name": "token'$index'",
            "identifier": "token'$index'",
            "description": "",
            "tags": {},
            "spec": {
                "value": "'$repoToken'",
                "secretManagerIdentifier": "harnessSecretManager",
                "valueType": "Inline"
            }
        }
    }')
    
    echo "\\n# adding github repository token as harness secret : token$index"
    echo "$response\\n"
done
 
 
 
# add github repository url as harness variable
response=$(curl --location "${url}/gateway/ng/api/variables?routingId=${accountId}&accountIdentifier=${accountId}" \
--header "Authorization: Bearer $token" \
--header "content-type: application/json" \
--data '{
    "variable": {
        "name": "repoUrl",
        "identifier": "repoUrl",
        "description": "",
        "type": "String",
        "spec": {
            "valueType": "FIXED",
            "fixedValue": "'$repoUrl'",
            "allowedValues": [],
            "defaultValue": ""
        }
    }
}')
echo "\\n# adding github repository url as harness variable : repoUrl"
echo "$response\\n"

# add github repository branch name as harness variable
response=$(curl --location "${url}/gateway/ng/api/variables?routingId=${accountId}&accountIdentifier=${accountId}" \
--header "Authorization: Bearer $token" \
--header "content-type: application/json" \
--data '{
    "variable": {
        "name": "repoBranchName",
        "identifier": "repoBranchName",
        "description": "",
        "type": "String",
        "spec": {
            "valueType": "FIXED",
            "fixedValue": "'$repoBranchName'",
            "allowedValues": [],
            "defaultValue": ""
        }
    }
}')
echo "\\n# adding github repository branch as harness variable : repoBranchName"
echo "$response\\n"

# add k8s cluster namespace as harness variable
response=$(curl --location "${url}/gateway/ng/api/variables?routingId=${accountId}&accountIdentifier=${accountId}" \
--header "Authorization: Bearer $token" \
--header "content-type: application/json" \
--data '{
    "variable": {
        "name": "k8sNamespace",
        "identifier": "k8sNamespace",
        "description": "",
        "type": "String",
        "spec": {
            "valueType": "FIXED",
            "fixedValue": "'$k8sNamespace'",
            "allowedValues": [],
            "defaultValue": ""
        }
    }
}')
echo "\\n# adding k8s cluster namespace as harness variable : k8sNamespace"
echo "$response\\n"



# ---------BEGIN: Create CD secrets and variables-----------------


# create AWS secret key secret
response=$(curl --location "$url/gateway/ng/api/v2/secrets?routingId=$accountId&accountIdentifier=$accountId" \
--header "Authorization: Bearer $token" \
--header "content-type: application/json" \
--data '{
    "secret": {
        "type": "SecretText",
        "name": "awssecretkey",
        "identifier": "awssecretkey",
        "description": "",
        "tags": {},
        "spec": {
            "value": "'$awssecretkey'",
            "secretManagerIdentifier": "harnessSecretManager",
            "valueType": "Inline"
        }
    }
}')

echo "\\n# adding AWS secret key as harness secret : awssecretkey"
echo "$response\\n"


# create AWS access key secret
response=$(curl --location "$url/gateway/ng/api/v2/secrets?routingId=$accountId&accountIdentifier=$accountId" \
--header "Authorization: Bearer $token" \
--header "content-type: application/json" \
--data '{
    "secret": {
        "type": "SecretText",
        "name": "awsaccesskey",
        "identifier": "awsaccesskey",
        "description": "",
        "tags": {},
        "spec": {
            "value": "'$awsaccesskey'",
            "secretManagerIdentifier": "harnessSecretManager",
            "valueType": "Inline"
        }
    }
}')

echo "\\n# adding AWS access key as harness secret : awsaccesskey"
echo "$response\\n"


response=$(curl --location "${url}/gateway/ng/api/variables?routingId=${accountId}&accountIdentifier=${accountId}" \
--header "Authorization: Bearer $token" \
--header "content-type: application/json" \
--data '{
    "variable": {
        "name": "manifestRepoUrl",
        "identifier": "manifestRepoUrl",
        "description": "",
        "type": "String",
        "spec": {
            "valueType": "FIXED",
            "fixedValue": "'$manifestRepoUrl'",
            "allowedValues": [],
            "defaultValue": ""
        }
    }
}')
echo "\\n# adding github k8s manifest repository url as harness variable : manifestRepoUrl"
echo "$response\\n"


response=$(curl --location "${url}/gateway/ng/api/variables?routingId=${accountId}&accountIdentifier=${accountId}" \
--header "Authorization: Bearer $token" \
--header "content-type: application/json" \
--data '{
    "variable": {
        "name": "manifestRepoCommitId",
        "identifier": "manifestRepoCommitId",
        "description": "",
        "type": "String",
        "spec": {
            "valueType": "FIXED",
            "fixedValue": "'$manifestRepoCommitId'",
            "allowedValues": [],
            "defaultValue": ""
        }
    }
}')
echo "\\n# adding github k8s manifest repository commit ID as harness variable : manifestRepoCommitId"
echo "$response\\n"


response=$(curl --location "${url}/gateway/ng/api/variables?routingId=${accountId}&accountIdentifier=${accountId}" \
--header "Authorization: Bearer $token" \
--header "content-type: application/json" \
--data '{
    "variable": {
        "name": "awsRegion",
        "identifier": "awsRegion",
        "description": "",
        "type": "String",
        "spec": {
            "valueType": "FIXED",
            "fixedValue": "'$awsRegion'",
            "allowedValues": [],
            "defaultValue": ""
        }
    }
}')
echo "\\n# adding AWS region as harness variable : awsRegion"
echo "$response\\n"


response=$(curl --location "${url}/gateway/ng/api/variables?routingId=${accountId}&accountIdentifier=${accountId}" \
--header "Authorization: Bearer $token" \
--header "content-type: application/json" \
--data '{
    "variable": {
        "name": "awsArtifactImage",
        "identifier": "awsArtifactImage",
        "description": "",
        "type": "String",
        "spec": {
            "valueType": "FIXED",
            "fixedValue": "'$awsArtifactImage'",
            "allowedValues": [],
            "defaultValue": ""
        }
    }
}')
echo "\\n# adding AWS ECR artifact image as harness variable : awsArtifactImage"
echo "$response\\n"


response=$(curl --location "${url}/gateway/ng/api/variables?routingId=${accountId}&accountIdentifier=${accountId}" \
--header "Authorization: Bearer $token" \
--header "content-type: application/json" \
--data '{
    "variable": {
        "name": "awsArtifactTag",
        "identifier": "awsArtifactTag",
        "description": "",
        "type": "String",
        "spec": {
            "valueType": "FIXED",
            "fixedValue": "'$awsArtifactTag'",
            "allowedValues": [],
            "defaultValue": ""
        }
    }
}')
echo "\\n# adding AWS ECR artifact tag as harness variable : awsArtifactTag"
echo "$response\\n"


# ---------END: Create CD secrets and variables-----------------
