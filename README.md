# Generating Proof-of-Concept Exploits for Vulnerable npm Packages

This repository contains a tool to generate proof-of-concept exploits for vulnerable npm packages.

### Building the Docker Image

1. Clone the repository:

```sh
$ git clone https://github.com/sola-st/PoCGen
```

2. Install dependencies:

```sh
$ cd PoCGen
$ npm install
```

3. Build the docker images:

```sh
$ docker build -t patched_node -f patched_node.Dockerfile .
$ docker build -t gen-poc_mnt .
```

### Setup

The repository contains a wrapper script to run the tool in a docker container.
The script requires an `.env` file in the current directory with the following content:

```
OPENAI_API_KEY=sk-proj-xxx
OPENAI_API_BASE_URL=https://open.bigmodel.cn/api/paas/v4  # Optional: for custom OpenAI-compatible API
GITHUB_API_KEY=github_pat_xxx # required for fetching GHSA-IDs

# Optional: Token limits per vulnerability (default: MAX_COMPLETION_TOKENS=100000, MAX_PROMPT_TOKENS=300000)
MAX_COMPLETION_TOKENS=100000  # Maximum output tokens per vulnerability
MAX_PROMPT_TOKENS=300000      # Maximum input tokens per vulnerability

# Optional: Timeout limits per vulnerability
VULN_TIMEOUT_SECONDS=3600     # Timeout for processing a single vulnerability in seconds (default: 3600 = 1 hour)
EXPLOIT_TIMEOUT_MS=60000      # Timeout for exploit test execution in milliseconds (default: 60000 = 1 minute)

# Optional: Model name configuration
MODEL_NAME=gpt-4o-mini         # Default model to use (must be a registered model name like "gpt-4o-mini" or "gpt-4o")
MODEL_NAME_OVERRIDE=glm-4.7    # Override the actual model name sent to API (e.g., "glm-4.7" for GLM-4 API)
```

**Note**: If you want to use a custom OpenAI-compatible API (instead of the official OpenAI API), set `OPENAI_API_BASE_URL` to your API base URL. For example, to use GLM-4 API, set it to `https://open.bigmodel.cn/api/paas/v4`.

**Model Configuration**: 
- `MODEL_NAME`: Selects the default model to use from registered models (e.g., "gpt-4o-mini", "gpt-4o"). This must match one of the registered model names in the project.
- `MODEL_NAME_OVERRIDE`: Overrides the actual model name sent to the API. This is useful when using custom APIs that support different model names (e.g., "glm-4.7" for GLM-4 API). If set, this value will be used in API calls instead of the registered model name.

**Token and Timeout Limits**: You can configure token limits and timeout limits for individual vulnerability processing through environment variables:
- `MAX_COMPLETION_TOKENS`: Maximum number of output tokens allowed per vulnerability (default: 100,000)
- `MAX_PROMPT_TOKENS`: Maximum number of input tokens allowed per vulnerability (default: 300,000)
- `VULN_TIMEOUT_SECONDS`: Maximum time allowed to process a single vulnerability in seconds (default: 3600 = 1 hour)
- `EXPLOIT_TIMEOUT_MS`: Maximum time allowed for exploit test execution in milliseconds (default: 60000 = 1 minute)

The only required argument is the vulnerability ID, which should be a GitHub Advisory ID or a Snyk ID.
The tool will automatically fetch the vulnerability report from the corresponding API/ scrape it from the website.

### Create a PoC for a vulnerable package

Run this script from the repository root:

```sh
$ ./run-mnt.sh output node index.js create -v GHSA-m7p2-ghfh-pjvx
```

This will create a test for [GHSA-m7p2-ghfh-pjvx](https://github.com/advisories/GHSA-m7p2-ghfh-pjvx) in
`./output/GHSA-m7p2-ghfh-pjvx/test.js`.

### Running the test

For most vulnerabilities, it is recommended to run the test using the provided docker image:

```sh
$ ./run-mnt.sh output node --test /output/<advisoryId>/test.js
```

For **ReDoS** vulnerabilities, the test should be run with the following flags:

```sh
./run-mnt.sh output node --test --enable-experimental-regexp-engine-on-excessive-backtracks --regexp-backtracks-before-fallback=30000 output/<advisoryId>/test.js
```

For vulnerabilities that involve long-running tasks (e.g. web servers), run the test with the following flags:

```sh
$ ./run-mnt.sh output node --test --test-force-exit /output/<advisoryId>/test.js
```

## Reproducing the Evaluation Results

First, follow the installation instructions above.

### RQ1: How effective is the approach?

```sh
$ ./run-mnt.sh output node index.js pipeline -v dataset/SecBench.js/*\.all
```

> Note that in our experiments, the approach was run twice (without caching prompts).

<div style="text-align: center;">
  <img src="figures/SecBench.js_tables.png" width="400px"/>
</div>

### RQ2: What is the impact of single components to the overall effectiveness of the approach?

The following table shows the different refiner configurations and which components are enabled or disabled.

| Refiner | Taint Path | Reference Exploits/ API Usage | ErrorRefiner | DebugRefiner | ContextRefiner |
|---------|------------|-------------------------------|--------------|--------------|----------------|
| $C_0$   | ❌          | ✅                             | ✅            | ✅            | ❌              |
| $C_1$   | ✅          | ❌                             | ✅            | ✅            | ✅              |
| $C_2$   | ✅          | ✅                             | ❌            | ✅            | ✅              |
| $C_3$   | ✅          | ✅                             | ✅            | ❌            | ✅              |
| $C_4$   | ✅          | ✅                             | ✅            | ✅            | ❌              |

A refiner can be specified using `--refiner <refiner>`, where `<refiner>` is one of the following values: `C0Refiner`,
`C1Refiner`, `C2Refiner`, `C3Refiner`, `C4Refiner`.

### RQ3: How efficient is the approach in terms of cost and time?

To reproduce the results for RQ3, run the following command:

```sh
$ ./run-mnt.sh output node index.js pipeline -v dataset/SecBench.js/*\.all
```
