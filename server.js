const express = require('express');
const app = express();
const port = 3000;

app.get('/', (req, res) => {
  res.send("Welcome to Adam's server for trading stocks")
});

app.post('/', (req, res) => {
  console.log(`Message: ${res}`)
});

const server = app.listen(port, () => {
  console.log(`HTTP server running on port ${port}!`)
});
