# courtbot 

Slack app providing slash commands for reserving squash courts.

## Quickstart

This project is intended to support a Slack app providing custom slash commands. It uses the [Serverless](https://github.com/serverless/serverless) framework to deploy a collection of AWS Lambda functions which constitute the service. For Serverless' AWS provider docs, see [here](https://serverless.com/framework/docs/providers/aws/).

To get started, create a [Slack app](https://api.slack.com/slack-apps). Then, configure your AWS [credentials](https://serverless.com/framework/docs/providers/aws/cli-reference/config-credentials/) so Serverless can find them. Install dependencies:

```sh
$ npm install
```

Development dependencies will be automatically excluded when the service is packaged for deployment. Before Serverless will deploy the service, it also needs to be able to find a secrets file named `secrets.dev.yml`. You can create this file yourself, or you can decrypt the included `secrets.dev.yml.encrypted` file:

```sh
$ npm run decrypt -- <your password here>
```

See `secrets.dev.yml.example` for an example of what the file should look like. If you create the file yourself, encrypt it with the following command to create a file you can commit:

```sh
$ npm run encrypt -- <your password here>
```

Now deploy the service:

```sh
$ npm run deploy
```

Configure slash commands (i.e., `/look` and `/book`) that POST to the deployed `router` endpoint.

## Design

Slack requires that "in channel" slash commands receive a response [within 3 seconds](https://api.slack.com/slash-commands#responding_to_a_command). I designed the courtbot service to meet this requirement in spite of Lambda's multi-second cold start time and the fact that booking can take upwards of 5 seconds.

I use [`serverless-plugin-warmup`](https://github.com/FidelLimited/serverless-plugin-warmup) to create a scheduled Lambda which invokes the `router` function every 5 minutes. The `router` function detects when it's been invoked by `serverless-plugin-warmup` and exits immediately. This protects the `router` function from cold starts and keeps execution time down. All slash commands are configured to POST to this "warm" endpoint. Since there's no cold start to deal with, the `router` can immediately invoke the long-running `look` and `book` functions (asynchronously) and return a response to Slack in under 3 seconds.

## Development

Use the function-specific `npm` scripts to deploy individual functions during development. This is faster than deploying the entire service. For example, to deploy only the router function:

```sh
$ npm run deploy:router
```

To run ESLint:

```sh
$ npm test
```

To see all available `npm` scripts:

```sh
$ npm run
```
