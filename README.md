# courtbot 

Slack app providing slash commands for reserving squash courts.

## Quickstart

This project is intended to support a Slack app providing custom [slash commands](https://api.slack.com/slash-commands). It uses [Zappa](https://github.com/Miserlou/Zappa) to deploy a [Flask](http://flask.pocoo.org/) application to [AWS Lambda](https://aws.amazon.com/lambda/) and [Amazon API Gateway](https://aws.amazon.com/api-gateway/).

To get started, create a [Slack app](https://api.slack.com/slack-apps). If you haven't already, create a local [AWS credentials file](https://aws.amazon.com/blogs/security/a-new-and-standardized-way-to-manage-credentials-in-the-aws-sdks/).

Install requirements:

```sh
$ make requirements
```

Package and deploy the service:

```sh
$ make deploy
```

Set environment variables the app needs to function:

```
MIT_RECREATION_PASSWORDS=your-password,another-password
MIT_RECREATION_USERNAMES=your-username,another-username
SLACK_TEAM_ID=your-slack-team-id
SLACK_VERIFICATION_TOKEN=your-slack-verification-token
```

Finally, configure slash commands (e.g., `/look` and `/book`) that POST to the `/look` and `/book` endpoints.

For information about additional Make targets:

```sh
$ make help
```

## Development

`courtbot` is a Flask app. It can be run locally without using Lambda:

```sh
$ make serve
```

Remember to export the necessary environment variables. If you want to use Slack to test `courtbot` changes running locally, use [ngrok](https://ngrok.com/) to expose the server running on your local machine to the Internet:

```sh
$ make tunnel
```

Use the public URL of your tunnel to configure development slash commands (e.g., `/dev-look` and `/dev-book`) that POST to the `https://<id>.ngrok.io/look` and `https://<id>.ngrok.io/book` endpoints.

To run the linter ([Flake8](http://flake8.pycqa.org/)):

```sh
$ make lint
```

## Design

Slack requires that "in channel" slash commands receive a response [within 3 seconds](https://api.slack.com/slash-commands#responding_to_a_command). `courtbot` uses Zappa's [auto keep-warm](https://github.com/Miserlou/Zappa#keeping-the-server-warm) and [asynchronous task execution](https://github.com/Miserlou/Zappa#asynchronous-task-execution) features to meet this requirement in spite of Lambda's multi-second cold start time and the fact that booking can take upwards of 5 seconds.
