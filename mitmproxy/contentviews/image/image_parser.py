import io
import typing

from kaitaistruct import KaitaiStream

from mitmproxy.contrib.kaitaistruct import png
from mitmproxy.contrib.kaitaistruct import gif
from mitmproxy.contrib.kaitaistruct import jpeg

Metadata = typing.List[typing.Tuple[str, str]]


def parse_png(data: bytes) -> Metadata:
    img = png.Png(KaitaiStream(io.BytesIO(data)))
    parts = [
        ('Format', 'Portable network graphics'),
        ('Size', "{0} x {1} px".format(img.ihdr.width, img.ihdr.height))
    ]
    for chunk in img.chunks:
        if chunk.type == 'gAMA':
            parts.append(('gamma', str(chunk.body.gamma_int / 100000)))
        elif chunk.type == 'pHYs':
            aspectx = chunk.body.pixels_per_unit_x
            aspecty = chunk.body.pixels_per_unit_y
            parts.append(('aspect', "{0} x {1}".format(aspectx, aspecty)))
        elif chunk.type == 'tEXt':
            parts.append((chunk.body.keyword, chunk.body.text))
        elif chunk.type == 'iTXt':
            parts.append((chunk.body.keyword, chunk.body.text))
        elif chunk.type == 'zTXt':
            parts.append((chunk.body.keyword, chunk.body.text_datastream.decode('iso8859-1')))
    return parts


def parse_gif(data: bytes) -> Metadata:
    img = gif.Gif(KaitaiStream(io.BytesIO(data)))
    descriptor = img.logical_screen_descriptor
    parts = [
        ('Format', 'Compuserve GIF'),
        ('Version', "GIF{}".format(img.header.version.decode('ASCII'))),
        ('Size', "{} x {} px".format(descriptor.screen_width, descriptor.screen_height)),
        ('background', str(descriptor.bg_color_index))
    ]
    ext_blocks = []
    for block in img.blocks:
        if block.block_type.name == 'extension':
            ext_blocks.append(block)
    comment_blocks = []
    for block in ext_blocks:
        if block.body.label._name_ == 'comment':
            comment_blocks.append(block)
    for block in comment_blocks:
        entries = block.body.body.entries
        for entry in entries:
            comment = entry.bytes
            if comment is not b'':
                parts.append(('comment', str(comment)))
    return parts


def parse_jpeg(data: bytes) -> Metadata:
    img = jpeg.Jpeg(KaitaiStream(io.BytesIO(data)))
    parts = [
        ('Format', 'JPEG (ISO 10918)')
    ]
    for segment in img.segments:
        if segment.marker._name_ == 'sof0':
            parts.append(('Size', "{0} x {1} px".format(segment.data.image_width, segment.data.image_height)))
        if segment.marker._name_ == 'app0':
            parts.append(('jfif_version', "({0}, {1})".format(segment.data.version_major, segment.data.version_minor)))
            parts.append(('jfif_density', "({0}, {1})".format(segment.data.density_x, segment.data.density_y)))
            parts.append(('jfif_unit', str(segment.data.density_units._value_)))
        if segment.marker._name_ == 'com':
            parts.append(('comment', str(segment.data)))
        if segment.marker._name_ == 'app1':
            if hasattr(segment.data, 'body'):
                for field in segment.data.body.data.body.ifd0.fields:
                    if field.data is not None:
                        parts.append((field.tag._name_, field.data.decode('UTF-8').strip('\x00')))
    return parts
