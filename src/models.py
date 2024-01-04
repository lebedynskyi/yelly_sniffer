from dataclasses import dataclass


@dataclass
class PostMeta:
    title: str
    url: str


@dataclass
class PostContent:
    title: str
    body: str
    orig_url: str
    image: str


class PostEntity:
    def __init__(self, local_id, date, title, orig_content, orig_url, own_url, image_url, rpc_status, fb_status):
        self.date = date
        self.fb_status = fb_status
        self.rpc_status = rpc_status
        self.local_id = local_id
        self.orig_url = orig_url
        self.own_url = own_url
        self.title = title
        self.orig_content = orig_content
        self.image = image_url
