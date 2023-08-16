

# inputs

url=http://<ip>
username=<username>
password=<password>
repoUserIds=("<userId1>" "<userId2>")
repoTokens=("<token1>" "<token2>")
repoUrl=<repoUrl>
organizationCount=<count>
projectCount=<count>


### ------ cd input variables BEGIN ------ 
# k8s manifest details
manifestRepoUrl=<manifestRepoUrl>
manifestRepoCommitId=<manifestRepoCommitId>
k8sClusterUrl=<k8sClusterUrl>

# ecr artifact details
awsRegion=<awsRegion>
awsArtifactImage=<awsArtifactImage>
awsArtifactTag=<awsArtifactTag>

cdDelegateSelector="perf-delegate"

# secrets
k8ssatoken=<k8ssatoken>
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

 
# Create Organizations and projects
 
orgUrl="$url/gateway/ng/api/organizations?accountIdentifier=$accountId"
projectUrl="$url/gateway/ng/api/projects?routingId=$accountId&accountIdentifier=$accountId&orgIdentifier="
 
for ((index = 1; index <= $organizationCount; index++)); do
    orgName="harness_organization_${index}"
 
    json_data='{
    "organization": {
        "name": "'"${orgName}"'",
        "description": "",
        "identifier": "'"${orgName}"'",
        "tags": {} } }'
 
    response=$(curl --location --request POST "$orgUrl" \
    --header "authorization: Bearer $token" \
    --header "content-type: application/json" \
    --data-raw "$json_data")
 
    echo "\\n# adding harness_organization_$index"
    echo "$response\\n"
 
    projectFinal="${projectUrl}${orgName}"
    for ((projectIndex = 1; $projectIndex <= $projectCount; projectIndex++)); do
        projectName="harness_project_${projectIndex}"
        json_data_project='{
        "project": {
            "name": "'"${projectName}"'",
            "orgIdentifier": "'"${orgName}"'",
            "color": "#0063f7",
            "description": "",
            "identifier": "'"${projectName}"'",
            "tags": {},
            "modules": [] } }'
    
        projectResponse=$(curl --location --request POST "$projectFinal" \
                --header "authorization: Bearer $token" \
                --header "content-type: application/json" \
                --data-raw "$json_data_project")
        
        echo "\\n# adding harness_project_$projectIndex in harness_organization_$index"
        echo "$projectResponse\\n"
    done
 
done
 
 
 
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



# ---------BEGIN: Create CD secrets and variables-----------------

# create k8s cluster SA token account level secret
response=$(curl --location "$url/gateway/ng/api/v2/secrets?routingId=$accountId&accountIdentifier=$accountId" \
--header "Authorization: Bearer $token" \
--header "content-type: application/json" \
--data '{
    "secret": {
        "type": "SecretText",
        "name": "k8ssatoken",
        "identifier": "k8ssatoken",
        "description": "",
        "tags": {},
        "spec": {
            "value": "'$k8ssatoken'",
            "secretManagerIdentifier": "harnessSecretManager",
            "valueType": "Inline"
        }
    }
}')

echo "\\n# adding k8s cluster SA token as harness secret : k8ssatoken"
echo "$response\\n"


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
        "name": "k8sClusterUrl",
        "identifier": "k8sClusterUrl",
        "description": "",
        "type": "String",
        "spec": {
            "valueType": "FIXED",
            "fixedValue": "'$k8sClusterUrl'",
            "allowedValues": [],
            "defaultValue": ""
        }
    }
}')
echo "\\n# adding k8s cluster url as harness variable : k8sClusterUrl"
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



response=$(curl --location "${url}/gateway/ng/api/variables?routingId=${accountId}&accountIdentifier=${accountId}" \
--header "Authorization: Bearer $token" \
--header "content-type: application/json" \
--data '{
    "variable": {
        "name": "cdDelegateSelector",
        "identifier": "cdDelegateSelector",
        "description": "",
        "type": "String",
        "spec": {
            "valueType": "FIXED",
            "fixedValue": "'$cdDelegateSelector'",
            "allowedValues": [],
            "defaultValue": ""
        }
    }
}')
echo "\\n# adding CD delegate selector as harness variable : cdDelegateSelector"
echo "$response\\n"


# ---------END: Create CD secrets and variables-----------------
