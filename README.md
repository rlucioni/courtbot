# courtbot 

Bot for checking squash court availability.

## Development

Create a new Slack [bot user](https://api.slack.com/bot-users). Retrieve your bot user's API token and put it in a new file, `.docker/env`. See `.docker/env.example` for an example. Other environment variables can be placed in this file to override default settings.

With Docker and Docker Compose installed and running, start the bot:

```
$ make up
```

If the image doesn't exist locally, Docker Compose will pull it from [Docker Hub](https://hub.docker.com/r/rlucioni/courtbot/) then start the `courtbot` service (i.e., container).

Tail service logs:

```
$ make logs
```

Open a shell on a one-off `courtbot` container:

```
$ make shell
```

Build a new `courtbot` image:

```
$ make build
```

For information about additional Make targets:

```
$ make help
```

## Deployment

Travis manages deployment. Travis builds a new image for every commit, on every branch. This image is used to run tests.

When changes are merged to master, Travis builds a new image as usual. However, it also pushes the new image to Docker Hub. Travis then assembles a build artifact and copies it to the production host, a DigitalOcean Droplet. Finally, Travis runs an update script included in the build artifact on the production host via SSH. The update script pulls new images from Docker Hub, stops all services, brings the services up again using fresh images and config, and deletes any unused images.

If you need to update deployed config, you'll need to create a new encrypted archive. Doing so requires installing the Travis CLI:

```
$ gem install travis
```

And logging into Travis:

```
$ travis login --org
```

Once you've done the above, make your change in `.docker/env`, then run `make encrypt`. Commit the updated `secrets.tar.enc` file.
