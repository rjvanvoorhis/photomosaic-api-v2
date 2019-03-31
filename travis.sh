#!/usr/bin/env bash
function set_home() {
    export PROJECT_PATH=$(pwd)
    export MOSAIC_API_PROJECT=photomosaic-api-v2
    export MOSAIC_MAKER_PROJECT=mock-mosaic-maker
    export TEST_PROJECT=photomosaic-bdds
}

function go_home() {
    cd ${PROJECT_PATH}
}

function get_project() {
    go_home
    git clone https://github.com/rjvanvoorhis/${1}
}

function setup_local() {
     set_home
     export PYTHONPATH=.:$PROJECT_PATH
     export ADMIN_USERNAME="behave_admin_user"
     export ADMIN_EMAIL="photomosaic.api.admin@gmail.com"
     export USER_USERNAME="behave_basic_user"
     export USER_EMAIL="photomosaic.api.user@gmail.com"
     export BEHAVE_USERNAME='behave_user'
     export BEHAVE_EMAIL='photomosaic.api@gmail.com'

     export MONGODB_URI=mongodb://mongodb:27017
     export S3_PORT=81
     export MOCK_MOSAIC_EXTERNAL_PORT=5080
     export S3_ENDPOINT_URL=http://local-s3:80/
     export s3_EXTERNAL_URL=http://localhost:${S3_PORT}
     export FAAS_URL=http://mock-mosaic-maker:5080
     export FRONT_END_URL=http:localhost
     export MOSAIC_API_URL_INTERNAL=http://mosaic-api:5000/api/v1/photomosaic
     export MOSAIC_API_URL_EXTERNAL=http://localhost:5000/api/v1/photomosaic
     export FRONT_END_URL=http://localhost
     export MOSAIC_API_PORT=5000
     export MONGODB_PORT=27018
     export S3_PORT=81
     export MEDIA_BUCKET=images
     export S3_EXTERNAL_URL=http://localhost:${S3_PORT}
     export HEALTHCHECK_URL=${MOSAIC_API_URL_EXTERNAL}/system/health_check
     export S3_VOLUME_DIR=${PROJECT_PATH}/photomosaic-bdds/s3_volume
     export MONGODB_VOLUME_DIR=${PROJECT_PATH}/photomosaic-bdds/mongodb_volume
}

function build_image() {
    go_home
    export BUILD_TIME=$(date +"%Y-%m-%dT%H-%M-%S")
    docker-compose build
    # docker build -t ${1}:${BUILD_TIME} -t ${1}:latest .
}

function get_dependencies() {
    go_home
    sudo apt-get install curl
    get_docker_compose
    pip3 install -r requirements.txt
    rm -rf ${TEST_PROJECT} # ensure a fresh copy of the tests
    get_project ${TEST_PROJECT}
    cd ${TEST_PROJECT}
    pip3 install -r requirements.txt
    go_home
}

function get_docker_compose() {
    # sudo apt-get update
    # sudo apt-get install -o Dpkg::Options::="--force-confold" --force-yes -y docker-engine
    sudo rm /usr/local/bin/docker-compose
    sudo curl -L "https://github.com/docker/compose/releases/download/1.23.1/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    docker-compose --version
}

function run_coverage() {
     go_home
     coverage run -m unittest discover tests
     export COVERAGE_STATUS=$?
     coverage report -m
}

function run_bdds() {
    cd ${PROJECT_PATH}/${TEST_PROJECT}
    behave
    export BDD_STATUS=${?}
}

function get_status_code() {
    echo $(curl -s -I -o /dev/null -w "%{http_code}" ${1})
}

function stop_containers() {
    docker stop $(docker ps -aq)
}

function launch_stack() {
    go_home
    stop_containers
    docker-compose down
    docker-compose up -d
    echo "Waiting 5 seconds for system to settle down."
    poll_stack
}

function create_media_folder() {
    curl --request PUT "${S3_EXTERNAL_URL}/${MEDIA_BUCKET}"
}

function register_admin_user() {
    curl --request POST ${MOSAIC_API_URL_EXTERNAL}/register \
        -H "Content-Type: application/json" \
        --data "{ \"username\": \"${ADMIN_USERNAME}\", \"password\": \"${BEHAVE_PASSWORD}\", \"email\": \"${ADMIN_EMAIL}\"}"
}

function validate_admin_user() {
    curl --request POST ${MOSAIC_API_URL_EXTERNAL}/validate \
        -H "Content-Type: application/json" \
        --data "{ \"username\": \"${ADMIN_USERNAME}\", \"password\": \"${BEHAVE_PASSWORD}\"}"
}

function login_admin_user() {
    curl --request POST ${MOSAIC_API_URL_EXTERNAL}/validate \
        -H "Content-Type: application/json" \
        --data "{ \"username\": \"${ADMIN_USERNAME}\", \"password\": \"${BEHAVE_PASSWORD}\"}"
}

function add_admin_role() {
    curl --request PATCH ${MOSAIC_API_URL_EXTERNAL}/users/${ADMIN_USERNAME}/role \
        -H "Content-Type: application/json" \
        --data '{"role": "ADMIN"}'
}


function poll_stack() {
    COUNTER=0
    while [[ ${COUNTER} -lt 10 ]]; do
	sleep 5
        load_base_data
	if [[ ${HEALTHCHECK_STATUS} = 200 ]]; then
            echo "Stack has launched successfully"
	    break
        else
	    echo "Stack is still starting up, waiting for another 5 seconds"
            let COUNTER=COUNTER+1
        fi
    done

}

function load_base_data() {
    export HEALTHCHECK_STATUS=$(get_status_code ${HEALTHCHECK_URL})
    if [[ ${HEALTHCHECK_STATUS} != 200 ]]; then
	if [[ $(curl ${HEALTHCHECK_URL} | jq -r '.s3_connection') != "SUCCESS" ]]; then
            create_media_folder
        fi
    else
        register_admin_user
	validate_admin_user
	add_admin_role
    fi
}

function travis_build() {
    setup_local
    get_dependencies
    run_coverage
    if [[ ${COVERAGE_STATUS} = 0 ]]; then
	echo "Unittests passed, building image and testing integration"
        build_image 
        launch_stack
	run_bdds
	if [[ ${BDD_STATUS} != 0 ]]; then
           echo "Unittests passed but Integration Tests have failed"
	fi
    else
        echo "Unittests have failed. Skipping build and Integration Tests"
    fi
    docker ps
}
