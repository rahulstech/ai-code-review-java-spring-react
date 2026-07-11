FROM public.ecr.aws/lambda/python:3.12

# Install Amazon Corretto 21 JDK (required for compiling Java source code via javac)
RUN dnf update -y && \
    dnf install -y java-21-amazon-corretto-devel && \
    dnf clean all

# Create necessary directories
RUN mkdir -p /tmp/source /tmp/report /tmp/build

# Set environment variables for directories
ENV TOOLS_ROOT=/tools
ENV SOURCE_ROOT=/tmp/source
ENV REPORT_ROOT=/tmp/report
ENV BUILD_ROOT=/tmp/build

# Copy tools and make tools executable
COPY tools ${TOOLS_ROOT}
RUN chmod +x ${TOOLS_ROOT}/pmd/bin/pmd ${TOOLS_ROOT}/spotbugs/bin/spotbugs

# Copy application source code
COPY app.py ${LAMBDA_TASK_ROOT}/app.py

# Copy requirements and install them
COPY requirements.txt ${LAMBDA_TASK_ROOT}/requirements.txt
RUN pip install --no-cache-dir -r ${LAMBDA_TASK_ROOT}/requirements.txt

# Set the CMD to the handler function (required by AWS Lambda Python base image)
CMD ["app.lambda_handler"]
