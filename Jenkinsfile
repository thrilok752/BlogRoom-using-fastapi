
def python = 'C:\\Users\\chota\\AppData\\Local\\Python\\pythoncore-3.14-64\\python.exe'
def docker = 'C:\\Users\\chota\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin\\docker.exe'


pipeline{
    agent any
    stages {
        stage("checkout"){
            steps{
                checkout scm
            }
        }

        stage("Verify Environment"){
            steps{
                bat "${python} --version"
                bat "${python} -m uv --version"
                bat "${docker} --version"
            }

        }

        stage("install dependencies"){
            steps{
                bat "${python} -m uv sync --locked"
            }
        }

        stage("Lint"){
            steps{
                bat "${python} -m uv run ruff check ."
            }
        }

        stage("Testing/Unit Test"){
            steps{
                bat "${python} -m uv run pytest"
            }
        }

        stage("Docker Build"){
            steps{
                bat "${docker} build -t fastapi-japp:latest ."
            }
        }

        stage("Run Container"){
            steps {
                bat """
                copy D:\\upskill\\fastapi\\blogger\\.env .env
                """
                bat "${docker} rm -f fastapi-japp"
                bat """
                ${docker} run -d ^
                --name fastapi-japp ^
                --env-file .env ^
                -p 8081:8080 ^
                fastapi-japp:latest
                """
            }
        }

        stage("Wait") {
            steps {
                sleep(time: 8, unit: "SECONDS")
            }
        }

        stage("Health"){
            steps {
                bat "curl.exe http://localhost:8081/health"
            }
        }

        stage("Docker Hub"){
            steps {
                withCredentials([usernamePassword(
                    credentialsId: "dockerblog",
                    usernameVariable: "DOCKER_USER"
                    passwordVariable: "DOCKER_PASS"
                )]) {
                    bat """
                    echo %DOCKER_PASS% | ${docker} login -u %DOCKER_USER% --password-stdin
                    """
                    bat """
                    ${docker} tag fastapi-japp:latest %DOCKER_USER%/fastapi-japp:latest
                    """
                    bat """
                    ${docker} push %DOCKER_USER%/fastapi-japp:latest
                    """
                }
            }
        }
    }
    post{
        always{
            bat "${docker} logs fastapi-japp"
            bat "${docker} rm -f fastapi-japp"
        }
        success{
            echo "========pipeline executed successfully ========"
        }
        failure{
            echo "========pipeline execution failed========"
        }
    }
}