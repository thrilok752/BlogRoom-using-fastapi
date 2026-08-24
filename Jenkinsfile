
def python = 'C:\\Users\\chota\\AppData\\Local\\Python\\pythoncore-3.14-64\\python.exe'
def docker = 'C:\\Users\\chota\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin\\${docker}.exe'


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
                bat "${docker} rm -f fastapi-japp"
                bat """
                ${docker} run -d ^
                ---name fastapi-japp ^
                -p 8081:8080 ^
                fastapi-japp:latest
                """
            }
        }

        stage("Health"){
            steps {
                bat "curl.exe http://localhost:8081/health"
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