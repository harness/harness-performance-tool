
# inputs

url=http://<ip>
username=<username> # should be part of harness usergroup
password=<password>

userCount=1
new_email_id_prefix="harness_perftest_"
new_email_id_domain="@test.com"
new_user_password="<random_password>"



# login 
b64Str=$(printf "%s" "$username:$password" | base64)
login_result_response=$(curl -s --location "$url/gateway/api/users/login" \
--header 'content-type: application/json' \
--data "{\"authorization\":\"Basic $b64Str\"}" \
-w "\n%{http_code}\n")
status_code=$(echo "$login_result_response" | awk 'END {print $0}')
accountId=(`echo ${login_result_response} | grep -o '"defaultAccountId":"[^"]*' | cut -d : -f2 | cut -d "\"" -f2`)
token=(`echo ${login_result_response} | grep -o '"token":"[^"]*' | cut -d : -f2 | cut -d "\"" -f2`)

if [ $status_code -ne 200 ]; then
    echo "LOGIN REQUEST FAILED.."
    echo $login_result_response
    exit -1
fi


# add Harness users
base_url="$url/gateway/ng/api/user/users?accountIdentifier=$accountId"
search_url="$url/gateway/ng/api/invites/aggregate?accountIdentifier=$accountId&pageIndex=0&pageSize=1000&sortOrders=lastModifiedAt%2CDESC&searchTerm="
inviteUrl="$url/gateway/ng/api/invites/internal/link?accountIdentifier=$accountId&inviteId="
signupUrl="$url/gateway/api/users/invites/ngsignin?accountId=$accountId&generation=NG"
 
content_type='Content-Type: application/json'
 
for ((index = 0; index < $userCount; index++)); do
    email="${new_email_id_prefix}${index}${new_email_id_domain}"

    echo "Inviting and Sign up for User: $email"
 
    json_data='{
        "emails": [
            "'"${email}"'"
        ],
        "roleBindings": [
          {
            "resourceGroupIdentifier": "_all_resources_including_child_scopes",
            "roleIdentifier": "_account_admin",
            "roleName": "Account Admin",
            "resourceGroupName": "All Resources Including Child Scopes",
            "managedRole": true
          }
        ]
    }'
 
    user_invite_response=$(curl -s --location "$base_url" \
    --header "authorization: Bearer $token" \
    --header "$content_type" \
    --data-raw "$json_data" \
    -w "\n%{http_code}\n")
    status_code=$(echo "$user_invite_response" | awk 'END {print $0}')

    if [ $status_code -ne 200 ]; then
        echo "USER INVITE REQUEST FAILED.."
        echo $user_invite_response
        exit -1
    fi


    ##
    search_urlfinal="${search_url}${email}"
    search_user_response=$(curl -s --location --request POST "$search_urlfinal" \
            --header "authorization: Bearer $token" \
            --header "$content_type" \
            -w "\n%{http_code}\n")    
    status_code=$(echo "$search_user_response" | awk 'END {print $0}')

    if [ $status_code -ne 200 ]; then
        echo "SEARCH USER REQUEST FAILED.."
        echo $search_user_response
        exit -1
    fi
 
    invite_id_from_search=$(echo "$search_user_response" | grep -o '"id":"[^"]*' | cut -d '"' -f4)


    ##
    inviteFinal="${inviteUrl}${invite_id_from_search}"    
    get_invite_id_response=$(curl -s --location --request GET "$inviteFinal" \
            --header "authorization: Bearer $token" \
            --header "$content_type" \
            -w "\n%{http_code}\n")
    status_code=$(echo "$get_invite_id_response" | awk 'END {print $0}')

    if [ $status_code -ne 200 ]; then
        echo "GET INVITE ID REQUEST FAILED.."
        echo $get_invite_id_response
        exit -1
    fi

    data_value=$(echo "$get_invite_id_response" | grep -o '"data":"[^"]*' | cut -d ':' -f2- | cut -d '"' -f2)
    token_from_url=$(echo "$data_value" | grep -o 'token=[^&]*' | cut -d '=' -f2)
 

    ##
    signup_user_response=$(curl -s --location --request PUT "$signupUrl" \
            --header "authorization: Bearer $token" \
            --header "Content-Type: application/json" \
            --data-raw '{
                "email":"'"$email"'",
                "name":"Harness User",
                "password":"'"$new_user_password"'",
                "token":"'"$token_from_url"'",
                "accountId":"'"$accountId"'"
            }' \
            -w "\n%{http_code}\n")
    status_code=$(echo "$signup_user_response" | awk 'END {print $0}')
 
    if [ $status_code -ne 200 ]; then
        echo "SIGNUP USER REQUEST FAILED.."
        echo $signup_user_response
        exit -1
    fi

    echo "\nSignup response for $email: $signup_user_response\n"
 
done
