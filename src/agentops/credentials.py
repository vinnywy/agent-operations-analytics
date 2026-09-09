from urllib.parse import urlsplit

from .common import run


def inspect(ops, online=False):
    config = ops.config()
    root = config["workspace"]
    result = {"git_author": "NOT_RUN", "remote": "NOT_RUN", "github_auth": "NOT_RUN"}
    author = run(["git", "-C", root, "config", "--get", "user.email"])
    result["git_author"] = "configured" if author.returncode == 0 and author.stdout.strip() else "not-configured"
    remote = run(["git", "-C", root, "config", "--get", "remote.origin.url"])
    if remote.returncode == 0:
        url = remote.stdout.strip()
        parsed = urlsplit(url) if "://" in url else None
        if parsed and (parsed.password or (parsed.username and parsed.scheme in ("http", "https"))):
            result["remote"] = "FAIL: possible-credential-in-url"
        elif parsed:
            result["remote"] = {"host": parsed.hostname, "scheme": parsed.scheme}
        elif "@" in url and ":" in url:
            result["remote"] = {"host": url.split("@", 1)[1].split(":", 1)[0], "scheme": "ssh"}
        else:
            result["remote"] = {"scheme": "local-or-unrecognized"}
    if online:
        auth = run(["gh", "api", "user", "--jq", ".login"], timeout=30)
        result["github_auth"] = {"result": "PASS", "login": auth.stdout.strip()} if auth.returncode == 0 else {"result": "ERROR"}
    result["note"] = "Autoria Git não comprova autenticação; leitura não altera hosts nem credenciais."
    return result
