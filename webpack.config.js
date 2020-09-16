const path = require('path');
const CopyWebpackPlugin = require('copy-webpack-plugin');

// assets.js
const Assets = require('./assets');

module.exports = {
    entry: {
        app: "./templates/base.html",
    },
    module: {
        rules: [
          { test: /\.html/, use: ['html-loader'] }
        ]
    },
    output: {
        path: __dirname + "/static/",
        //filename: "[name].bundle.js"
    },
    plugins: [
      new CopyWebpackPlugin(
        Assets.map(asset => {
          return {
            from: path.resolve(__dirname, `./node_modules/${asset}`),
            to: path.resolve(__dirname, './static')
          };
        })
      )
    ]
};