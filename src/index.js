const querystring = require('querystring')
const request = require('request')
// Globally available in AWS Lambda
const aws = require('aws-sdk')
const utils = require('./utils.js')
const Scheduler = require('./scheduler.js')

// TODO: Keep this layer specific to AWS Lambda. Separate code for parsing and
// building messages.
// https://docs.aws.amazon.com/lambda/latest/dg/nodejs-prog-model-handler.html
module.exports.router = (event, context, callback) => {
  if (event.source === 'serverless-plugin-warmup') {
    console.log('Staying warm')
    return callback()
  }

  const input = querystring.parse(event.body)
  console.log(`Called by ${input.command} command`)

  if (!utils.isValid(input)) return callback(null, {statusCode: 400})

  let params = {
    FunctionName: null,
    InvocationType: 'Event',
    Payload: JSON.stringify(input),
  }

  let output = {
    response_type: 'in_channel',
    text: null,
  }

  if (input.command === '/look') {
    if (input.text.includes('help')) {
      output.text =
        'Use this command to check squash court availability. ' +
        'Call it without arguments (i.e., `/look`) to check today. ' +
        'Call it with `tomorrow` as an argument (e.g., `/look tomorrow`) to check tomorrow.'

      const response = {
        statusCode: 200,
        body: JSON.stringify(output),
      }

      return callback(null, response)
    }

    output.text = 'Looking...'
    params.FunctionName = 'courtbot-dev-look'
  } else if (input.command === '/book') {
    if (input.text.includes('help')) {
      output.text =
        'Use this command to reserve a Z-Center squash court. ' +
        'Call it with a court number and an hour to make a reservation (e.g., `/book #4 @ 8 pm`). ' +
        'Include `tomorrow` as an argument (e.g., `/book #4 @ 8 pm tomorrow`) to book a court for tomorrow.'

      const response = {
        statusCode: 200,
        body: JSON.stringify(output),
      }

      return callback(null, response)
    }

    output.text = 'Booking...'
    params.FunctionName = 'courtbot-dev-book'
  } else {
    // Unrecognized slash command.
    return callback(null, {statusCode: 400})
  }

  const lambda = new aws.Lambda()

  // http://docs.aws.amazon.com/AWSJavaScriptSDK/latest/AWS/Lambda.html#invoke-property
  lambda.invoke(params, (error, data) => {
    if (error) {
      console.error(error)

      output.text = 'Something went wrong. Sorry!'

      const response = {
        statusCode: 200,
        body: JSON.stringify(output),
      }

      return callback(null, response)
    }

    // All responses will be delayed. This prevents Slack from showing the invoking
    // user a timeout error (slash command timeout is 3 seconds).
    const response = {
      statusCode: 200,
      body: JSON.stringify(output),
    }

    callback(null, response)
  })
}

module.exports.look = (event, context) => {
  console.log(`Invoked with ${JSON.stringify(event)}`)
  const body = {
    response_type: 'in_channel',
    text: null,
  }

  const options = {
    url: event.response_url,
    json: true,
    body,
  }

  const s = new Scheduler()
  const isTomorrow = event.text.includes('tomorrow')

  s.look(isTomorrow).then(b => {
    const raw = b.d.Value
    const courts = utils.toHours(raw, isTomorrow)

    if (courts.size) {
      let message = [`Here's how the courts look${isTomorrow ? ' tomorrow' : ''}.`]

      for (let [courtNumber, hours] of courts) {
        message.push(`*#${courtNumber}* is available at ${hours}.`)
      }

      body.text = message.join('\n\n')
    } else {
      body.text = `There are no courts available${isTomorrow ? ' tomorrow' : ''}.`
    }

    request.post(options, (..._) => {})
  }).catch(error => {
    console.error(error)

    body.text = 'Something went wrong. Sorry!'
    request.post(options, (..._) => {})
  })
}

module.exports.book = (event, context) => {
  console.log(`Invoked with ${JSON.stringify(event)}`)
  const body = {
    response_type: 'in_channel',
    text: null,
  }

  const options = {
    url: event.response_url,
    json: true,
    body,
  }

  // https://regex101.com
  const re = /#([1-5]).*(@|at) ([1-9]|1[012])\s*(am|pm)/gi
  const match = re.exec(event.text)

  if (match) {
    const courtNumber = parseInt(match[1])
    const twelveHourTime = parseInt(match[3])
    const period = match[4].toUpperCase()

    const hour = utils.convertClock(`${twelveHourTime} ${period}`)

    const isTomorrow = event.text.includes('tomorrow')

    console.log('Ready to book')
    const s = new Scheduler()
    s.book(courtNumber, hour, isTomorrow).then(_ => {
      body.text = `All set! I've booked #${courtNumber} at ${twelveHourTime} ${period}${isTomorrow ? ' tomorrow' : ''}.`
      request.post(options, (..._) => {})
    }).catch(errors => {
      for (let error of errors) {
        console.error(error)
      }

      body.text = 'Something went wrong. Sorry!'
      request.post(options, (..._) => {})
    })
  } else {
    body.text = 'Please provide a court number and an hour (e.g., `/book #4 @ 8 pm`).'
    request.post(options, (..._) => {})
  }
}
