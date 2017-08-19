# courtbot 

Slack app providing slash commands for reserving squash courts.

## Quickstart

This project is intended to support a Slack app providing custom slash commands. It uses the [Serverless](https://github.com/serverless/serverless) framework. For AWS provider docs, see [here](https://serverless.com/framework/docs/providers/aws/).

To get started, create a [Slack app](https://api.slack.com/slack-apps). Then, configure your AWS [credentials](https://serverless.com/framework/docs/providers/aws/cli-reference/config-credentials/) so Serverless can find them.

Serverless also needs to be able to find a secrets file at `courtbot/secrets.dev.yml` to deploy the service. You can create this file yourself, or you can decrypt the included `courtbot/secrets.dev.yml.encrypted` file:

```sh
$ npm run decrypt -- <your password here>
```

If you create the file yourself, encrypt it with the following command to create a file you can commit:

```sh
$ npm run encrypt -- <your password here>
```

Finally, install courtbot's dependencies so they can be packaged with the service, then deploy the service (i.e., create the Lambdas):

```sh
$ cd courtbot && npm install
$ cd .. && npm run deploy
```

Configure slash commands that POST to the deployed `router` endpoint.

## Development

Use the function-specific `npm` scripts to deploy specific functions during development. This is faster than deploying the entire service. For example, to deploy only the router function:

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
