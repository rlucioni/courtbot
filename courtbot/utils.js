const moment = require('moment-timezone')

module.exports.isValid = data => {
  // Verify that a given request was issued by Slack.
  const slackVerificationToken = process.env.SLACK_VERIFICATION_TOKEN
  const slackTeamId = process.env.SLACK_TEAM_ID

  return data.token === slackVerificationToken && data.team_id === slackTeamId
}

module.exports.convertClock = twelveHourString => {
  // Convert a string representing an hour on a 12-hour clock into an integer
  // hour on a 24-hour clock.
  const twentyFourHours = Array.from(Array(24), (_, k) => k)
  const hours = new Map(twentyFourHours.map(hour => [moment().hour(hour).format('h A'), hour]))

  return hours.get(twelveHourString)
}

module.exports.toHours = (raw, isTomorrow) => {
  // Convert raw court availability data to an object of available hours keyed
  // by court number. This function expects an array of raw court availability
  // objects as returned by the scheduling API, each looking like:
  // {
  //   Id: 17,
  //   Availability: [
  //     {IsAvailable: false, TimeId: 0},
  //     {IsAvailable: false, TimeId: 1},
  //     ...
  //     {IsAvailable: false, TimeId: 1439},
  //   ]
  // }
  const hoursAsMinutes = new Set(Array.from(Array(24), (_, k) => k * 60))
  const tz = 'America/New_York'

  let courts = new Map()

  for (let court of raw) {
    let hours = []
    let minutes = court.Availability

    for (let minute of minutes) {
      if (hoursAsMinutes.has(minute.TimeId) && minute.IsAvailable) {
        let hour = minute.TimeId / 60

        // Exclude times that are in the past unless asked for times tomorrow.
        if (hour > moment().tz(tz).hour() || isTomorrow) hours.push(hour)
      }
    }

    if (hours.length) {
      // Join array of integers representing hours on a 24-hour clock into string
      // of comma-separated hours on a 12-hour clock.
      const formatted = hours.map(hour => moment().hour(hour).format('h A'))
      courts.set(court.Id - 16, formatted.join(', '))
    }
  }

  return courts
}
