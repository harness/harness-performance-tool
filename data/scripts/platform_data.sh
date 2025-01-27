

# inputs

url=http://<ip> # https://12.1.2.31
username=<username> # harness username
password=<password> # harness user password
organizationCount=<count> # 5
projectCount=<count> # 2 (per organization)

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
