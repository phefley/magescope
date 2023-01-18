# magescope
A CLI tool for inventorying and evaluating JavaScript resources present on a URL.

## Why is this important?

If you're trying to understand what resources a page loads, especially those loaded from other domains, you can look at the HTML, but that's only the tip of the iceberg. Additional JavaScript resources may be susequently loaded in to the DOM by the first stage scripts.

This tool helps model that by driving Selenium to obtain the page, model the DOM, look for loaded JavaScript resources, and present them.

## Why a CLI version?

I use this tool for my research (BSides DFW 2019) to demonstrate the prevalance of subsequent JavaScript resource loads. You can use my Burp extension (https://github.com/phefley/burp-javascript-security-extension) if that's easier for you - but some folks just need a quick check.

## Getting started with Docker

### Build the docker magescope image
docker build --tag magescope:v1 -f Dockerfile .

### Use the docker magescope image
docker container run --rm magescope:v1 --target https://www.someurlofinterest.com/path/

