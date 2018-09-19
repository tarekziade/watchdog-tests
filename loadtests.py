#!/usr/bin/env python
import io
from aiohttp import MultipartWriter, StreamReader
import urllib
import os
from mohawk import Sender
import molotov

if 'HAWK_KEY' not in os.environ:
    raise Exception('You need to set the HAWK_KEY environ')

image = 'images/book.jpg'
url = 'https://watchdogproxy-default.stage.mozaws.net'
path = '/accept'

negative_uri = 'https://webhook.site/8550f8d5-6da3-41de-8609-f7d0690bd6ff'
positive_uri = 'https://webhook.site/8550f8d5-6da3-41de-8609-f7d0690bd6ff'
positive_email = 'mbrandt@mozilla.com'

id = 'demouser'
key = '<key>'

hawk_config = {'id': 'demouser',
               'key': os.environ.get('HAWK_KEY'),
               'algorithm': 'sha256'}


def get_bits(image):
    with open(image, 'rb') as f:
        return f.read()

image_data = get_bits(image)

form_data = {
    'negative_uri': negative_uri,
    'positive_uri': positive_uri,
    'positive_email': positive_email,
}



async def get_content(writer):
    class Streamer:
        stream = io.BytesIO()
        async def write(self, data):
            self.stream.write(data)

    await writer.write(Streamer())
    Streamer.stream.seek(0)

    return Streamer.stream.read()


@molotov.scenario(weight=100)
async def test_simple(session):

    with MultipartWriter('form-data') as writer:
        writer.append_form(form_data)
        writer.append(io.BytesIO(image_data), {'Content-Type': 'image/jpeg'})

        raw = await get_content(writer)
        sender = Sender(hawk_config, url + path, 'POST',
                        content=raw,
                        content_type='multipart/form-data')

        headers = {'Authorization': sender.request_header}
        async with session.post(url + path,
                                data=raw,
                                headers=headers) as resp:
            assert resp.status_code is 201, resp.status_code
