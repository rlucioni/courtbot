# courtbot 

Slack app providing slash commands for reserving squash courts.

## Quickstart

This project is intended to support a Slack app providing custom slash commands. It uses the [Serverless](https://github.com/serverless/serverless) framework. For AWS provider docs, see [here](https://serverless.com/framework/docs/providers/aws/).

To get started, create a [Slack app](https://api.slack.com/slack-apps). Next, configure your AWS [credentials](https://serverless.com/framework/docs/providers/aws/cli-reference/config-credentials/), so Serverless can find them. Finally, install courtbot's dependencies so they can be packaged with the service, then deploy the service (i.e., create the Lambdas):

```sh
$ cd courtbot && npm install
$ cd .. && npm run deploy
```

Configure slash commands that POST to the deployed `router` endpoint.

To run ESLint:

    $ npm run lint

To see other `npm` scripts:

    $ npm run
