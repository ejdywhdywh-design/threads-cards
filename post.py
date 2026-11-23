# 클라우드 게시 루틴이 쓰는 Threads 게시 스크립트.
# 토큰은 다루지 않는다: 클라우드 환경의 네트워크 시크릿이 graph.threads.net 요청에 Authorization 헤더를 붙인다.
# 사용: python3 post.py <글.txt> [이미지URL] [--poll <선택지.json>] [--tag <주제태그>]
#       python3 post.py check-image <이미지URL> | check-poll [주제태그]   (둘 다 게시 안 함)
# 투표(--poll, 선택지 2~4개 JSON 배열)는 글만 있는 게시물에만 붙으므로, 투표가 있으면 이미지는 쓰지 않는다.
import json, sys, time, urllib.error, urllib.parse, urllib.request
API = "https://graph.threads.net/v1.0"
def out(**kw):
    print(json.dumps(kw, ensure_ascii=False)); sys.exit(0 if kw.get("ok") else 1)
def call(method, url, params):
    data = None
    if method == "GET":
        url += "?" + urllib.parse.urlencode(params)
    else:
        data = urllib.parse.urlencode(params).encode()
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=data, method=method), timeout=60) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code}: {e.read().decode('utf-8','replace')[:300]}") from None
    except urllib.error.URLError as e:
        raise RuntimeError(f"네트워크 오류: {e.reason}") from None
def create(params):
    return call("POST", f"{API}/me/threads", params)["id"]
def container(text, image_url, poll=None, tag=None):
    """컨테이너를 만든다. 반환: (id, 실제로 붙은 태그, 태그 오류)"""
    params = {"media_type": "TEXT", "text": text}
    if poll:
        image_url = None
        params["poll_attachment"] = json.dumps(dict(zip(["option_a", "option_b", "option_c", "option_d"], poll)), ensure_ascii=False)
    elif image_url:
        params.update(media_type="IMAGE", image_url=image_url)
    tag_error = None
    if tag:
        params["topic_tag"] = tag
    try:
        cid = create(params)
    except (RuntimeError, KeyError) as e:
        if not tag:
            raise
        # 아직 게시 전이라 태그만 빼고 다시 만들어도 중복 게시 위험이 없다
        tag_error, tag = str(e)[:150], None
        params.pop("topic_tag")
        cid = create(params)
    for _ in range(12 if image_url else 1):
        time.sleep(5)
        if not image_url:
            return cid, tag, tag_error
        st = call("GET", f"{API}/{cid}", {"fields": "status,error_message"})
        if st.get("status") == "FINISHED":
            return cid, tag, tag_error
        if st.get("status") in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"이미지 처리 실패: {st.get('error_message') or st.get('status')}")
    raise RuntimeError("이미지 처리가 60초 안에 끝나지 않았어요")
if sys.argv[1] == "check-image":
    try:
        out(ok=True, container=container("이미지 확인용 (게시 안 함)", sys.argv[2])[0], published=False)
    except (RuntimeError, KeyError) as e:
        out(ok=False, error=str(e))
if sys.argv[1] == "check-poll":
    try:
        cid, tag, tag_error = container("투표 확인용 (게시 안 함)", None, ["밀면", "냉면"], sys.argv[2] if len(sys.argv) > 2 else None)
        out(ok=True, container=cid, published=False, tag=tag, tagError=tag_error)
    except (RuntimeError, KeyError) as e:
        out(ok=False, error=str(e))
args, poll, tag = [], None, None
it = iter(sys.argv[1:])
for a in it:
    if a == "--poll":
        poll = json.load(open(next(it), encoding="utf-8"))
    elif a == "--tag":
        tag = next(it).strip().lstrip("#") or None
    else:
        args.append(a)
text = open(args[0], encoding="utf-8").read().strip()
image_url = args[1] if len(args) > 1 else None
if not text or len(text) > 500:
    out(ok=False, error=f"글 길이 문제: {len(text)}자")
if poll is not None and not (2 <= len(poll) <= 4 and all(isinstance(o, str) and 1 <= len(o) <= 25 for o in poll)):
    out(ok=False, error="투표 선택지는 2~4개, 각 1~25자여야 해요")
image_error = None
try:
    try:
        cid, tag, tag_error = container(text, image_url, poll, tag)
    except (RuntimeError, KeyError) as e:
        if not image_url or poll:
            raise
        # 아직 게시 전이라 글만으로 다시 만들어도 중복 게시 위험이 없다
        image_error = str(e)[:200]
        cid, tag, tag_error = container(text, None, None, tag)
    p = call("POST", f"{API}/me/threads_publish", {"creation_id": cid})
except (RuntimeError, KeyError) as e:
    out(ok=False, error=str(e))
link = None
try:
    link = call("GET", f"{API}/{p['id']}", {"fields": "permalink"}).get("permalink")
except RuntimeError:
    pass
out(ok=True, id=p.get("id"), permalink=link, image=bool(image_url and not image_error and not poll),
    imageError=image_error, poll=bool(poll), tag=tag, tagError=tag_error)
