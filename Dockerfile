# aws ecr get-login-password --region us-west-1 | docker login --username AWS --password-stdin 081924037451.dkr.ecr.us-west-1.amazonaws.com
# docker buildx build --platform linux/amd64 -t get-communities .
# docker tag get-communities:latest 081924037451.dkr.ecr.us-west-1.amazonaws.com/get-communities:latest
# docker push 081924037451.dkr.ecr.us-west-1.amazonaws.com/get-communities:latest

FROM public.ecr.aws/lambda/python:3.8

# Copy function code
COPY app.py ${LAMBDA_TASK_ROOT}

# Install the function's dependencies using file requirements.txt
# from your project folder.

COPY requirements.txt  .
RUN  pip3 install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"