import argparse
import os
import sys
import sqlite3
from pathlib import Path

from . import __version__
from .common import OpsError, confirm, encode, read_json
from .operations import Operations


def parser():
    root = argparse.ArgumentParser(prog="agentops", description="Operação local com evidências e revisões proporcionais.")
    root.add_argument("--version", action="version", version=__version__)
    root.add_argument("--home", default=os.environ.get("AGENTOPS_HOME"), help="Área pessoal externa à instalação; alternativa: AGENTOPS_HOME")
    commands = root.add_subparsers(dest="command", required=True)
    p = commands.add_parser("onboard", help="Configurar instalação e preferências de modo idempotente")
    p.add_argument("--source", help="Clone oficial contendo policy/operating-protocol.md")
    p.add_argument("--workspace")
    p.add_argument("--name")
    p.add_argument("--repository", help="Destino oficial GitHub owner/repo")
    commands.add_parser("doctor", help="Diagnóstico local por capacidade")
    commands.add_parser("activate", help="Registrar diagnóstico; não ativa ferramentas ocultas")
    p = commands.add_parser("integrate", help="Prévia da integração no workspace")
    p.add_argument("--apply", action="store_true")
    commands.add_parser("client-smoke", help="Registrar confirmação humana após teste em sessão nova")
    p = commands.add_parser("context", help="Contexto mínimo, sem carregar toda a documentação")
    p.add_argument("--task")
    p = commands.add_parser("status", help="Estado e relatório local")
    p.add_argument("--task")
    p = commands.add_parser("sprint", help="Cadastrar sprint explícita")
    p.add_argument("title")
    p.add_argument("--objective", required=True)
    p.add_argument("--period", default="not-confirmed")
    p = commands.add_parser("task", help="Ciclo de trabalho")
    sub = p.add_subparsers(dest="action", required=True)
    q = sub.add_parser("start")
    q.add_argument("--briefing", required=True, help="Arquivo JSON conforme task.schema.json")
    q = sub.add_parser("move")
    q.add_argument("id")
    q.add_argument("state", choices=["active", "validating", "blocked", "cancelled"])
    q = sub.add_parser("close")
    q.add_argument("id")
    p = commands.add_parser("evidence", help="Vincular arquivo a critério; não é prova semântica")
    p.add_argument("task")
    p.add_argument("--criterion", type=int, required=True)
    p.add_argument("--file", required=True)
    p = commands.add_parser("check-register", help="Cadastrar comando e entradas após confirmação")
    p.add_argument("name")
    p.add_argument("--argv", required=True, help="Arquivo JSON contendo array de argumentos")
    p.add_argument("--input", action="append", required=True)
    p = commands.add_parser("check", help="Executar checks registrados para a task")
    p.add_argument("task")
    p.add_argument("--timeout", type=int, default=120)
    p = commands.add_parser("review", help="Revisão opcional; sem execução implícita")
    sub = p.add_subparsers(dest="action", required=True)
    for kind in ("code", "notebook", "leakage", "security"):
        q = sub.add_parser(kind, help="Preparar oferta com arquivos explícitos")
        q.add_argument("--task", required=True)
        q.add_argument("--depth", choices=["targeted", "deep"], default="targeted")
        q.add_argument("--file", action="append", required=True)
        q.add_argument("--reason", required=True)
        q.add_argument("--max-chars", type=int, default=24000)
    q = sub.add_parser("decide")
    q.add_argument("id")
    q.add_argument("decision", choices=["accepted", "declined"])
    q.add_argument("--model")
    q.add_argument("--timeout", type=int, default=120)
    q = sub.add_parser("run")
    q.add_argument("id")
    q.add_argument("--model", required=True)
    q.add_argument("--timeout", type=int, default=120)
    q.add_argument("--execute", action="store_true")
    p = commands.add_parser("rfc", help="RFC local e publicação controlada")
    sub = p.add_subparsers(dest="action", required=True)
    q = sub.add_parser("draft")
    q.add_argument("file")
    q = sub.add_parser("publish")
    q.add_argument("id")
    q.add_argument("--execute", action="store_true")
    p = commands.add_parser("eval", help="Evals comportamentais opcionais; padrão NOT_RUN")
    p.add_argument("--model")
    p.add_argument("--execute", action="store_true")
    p.add_argument("--timeout", type=int, default=60)
    p = commands.add_parser("manifest", help="Gerar/verificar manifesto local; geração não autentica")
    p.add_argument("action", choices=["build", "verify"])
    p.add_argument("--source", required=True)
    p.add_argument("--release", default=__version__)
    p = commands.add_parser("update", help="Preparar release assinada em instalação separada")
    p.add_argument("--candidate", required=True)
    p.add_argument("--allowed-signers", required=True)
    p.add_argument("--identity", required=True)
    commands.add_parser("backup", help="Snapshot SQLite consistente")
    p = commands.add_parser("credentials", help="Inspecionar identidade/remotes sem exibir segredos")
    p.add_argument("--online", action="store_true", help="Verificar conta GitHub com chamada read-only")
    p = commands.add_parser("trust", help="Verificar assinatura e cadastrar identidade confiável")
    p.add_argument("--allowed-signers", required=True)
    p.add_argument("--identity", required=True)
    return root


def dispatch(args, ops):
    from . import evaluations, releases, reviews, rfcs
    command = args.command
    if command == "onboard":
        workspace = args.workspace or input("Caminho do workspace: ")
        name = args.name or input("Como deseja ser chamado(a)? ")
        source = Path(args.source) if args.source else Path.cwd()
        if not (source / "policy" / "operating-protocol.md").is_file():
            raise OpsError("SOURCE_REQUIRED: execute no clone oficial ou informe --source para um clone válido.")
        return ops.onboard(source, workspace, name, args.repository)
    if command in ("doctor", "activate"):
        return getattr(ops, command)()
    if command == "integrate":
        preview = ops.integration()
        if args.apply:
            print(encode(preview))
            confirm("Aplicar estes arquivos preservando cópia anterior?")
            return ops.integration(True)
        return preview
    if command == "client-smoke":
        integrations = ops.store.list("integration", 1)
        if not integrations:
            raise OpsError("Integração ainda não instalada.")
        confirm("Em sessão nova, confirmou protocolo, home, skills e uma task simulada conforme docs/onboarding.md?")
        identifier = ops.store.put("client-smoke", {"passed": True, "source": "human-attestation", "integration_id": integrations[0]["id"]})
        return {"id": identifier, "note": "Atestado humano, não eval automatizado."}
    if command in ("context", "status"):
        return getattr(ops, command)(args.task)
    if command == "sprint":
        return {"sprint": ops.store.put("sprint", {"title": args.title, "objective": args.objective, "period": args.period})}
    if command == "task":
        if args.action == "start":
            return ops.start(read_json(args.briefing))
        if args.action == "move":
            return ops.transition(args.id, args.state)
        return ops.close_task(args.id)
    if command == "evidence":
        return ops.evidence(args.task, args.criterion, args.file)
    if command == "check-register":
        argv = read_json(args.argv)
        if not isinstance(argv, list) or not all(isinstance(x, str) and x for x in argv):
            raise OpsError("argv deve ser array de strings não vazias.")
        print(encode({"argv": argv, "inputs": args.input}))
        confirm("Autorizar execução deste comando no workspace? Ele pode executar código do workspace.")
        return ops.configure_check(args.name, argv, args.input)
    if command == "check":
        if not 1 <= args.timeout <= 600:
            raise OpsError("Timeout deve estar entre 1 e 600s.")
        return ops.check(args.task, args.timeout)
    if command == "review":
        if args.action == "decide":
            if args.decision == "accepted":
                value = ops.store.get("review", args.id)
                print(encode(dict({k: v for k, v in value.items() if k != "packet"}, model=args.model, timeout=args.timeout)))
                confirm("Aceitar este escopo de revisão opcional?")
            return reviews.decide(ops, args.id, args.decision, args.model, args.timeout)
        if args.action == "run":
            preview = reviews.execute(ops, args.id, args.model, False, args.timeout)
            if args.execute:
                return reviews.execute(ops, args.id, args.model, True, args.timeout)
            return preview
        return reviews.plan(ops, args.task, args.action, args.depth, args.file, args.reason, args.max_chars)
    if command == "rfc":
        if args.action == "draft":
            return rfcs.draft(ops, read_json(args.file))
        preview = rfcs.publish(ops, args.id)
        if args.execute:
            print(encode(preview))
            confirm("Publicar este conteúdo exato neste destino? Confirme também ausência de dados privados.")
            return rfcs.publish(ops, args.id, True)
        return preview
    if command == "eval":
        if args.execute:
            print(encode(evaluations.evaluate(ops.config()["source"], ops.home, args.model)))
            confirm("Executar suíte LLM opcional, consumindo cota?")
        return evaluations.evaluate(ops.config()["source"], ops.home, args.model, args.execute, args.timeout)
    if command == "update":
        confirm("Preparar release assinada e backup local? A instalação ativa não será substituída.")
        return releases.stage_update(ops, args.candidate, args.allowed_signers, args.identity)
    if command == "backup":
        return {"backup": ops.store.backup()}
    if command == "credentials":
        from .credentials import inspect
        return inspect(ops, args.online)
    if command == "trust":
        result = releases.verify_signature(ops.config()["source"], args.allowed_signers, args.identity)
        print(encode(result))
        confirm("Confiar nesta identidade/chave para esta instalação? Verifique a chave por canal independente.")
        config = ops.config()
        config["trust"] = {"allowed_signers": str(Path(args.allowed_signers).resolve()), "identity": args.identity}
        from .common import atomic_write
        atomic_write(ops.home / "installation.json", encode(config))
        return result
    raise OpsError("Comando desconhecido.")


def main(argv=None):
    args = parser().parse_args(argv)
    ops = None
    try:
        if args.command == "manifest":
            from .releases import build_manifest, verify_manifest
            result = build_manifest(args.source, args.release) if args.action == "build" else verify_manifest(args.source)
        else:
            if not args.home:
                if args.command != "onboard" or not sys.stdin.isatty():
                    raise OpsError("Informe --home ou AGENTOPS_HOME (diretório pessoal externo).")
                args.home = input("Diretório pessoal externo à instalação e ao workspace: ")
            ops = Operations(args.home)
            result = dispatch(args, ops)
        print(encode(result))
        if result.get("state") in ("BLOCKED", "FAIL", "ERROR"):
            return 2
        if "results" in result and any(x.get("result") in ("FAIL", "ERROR") for x in result["results"]):
            return 2
        return 0
    except (OpsError, ValueError, OSError, KeyError, sqlite3.Error) as exc:
        # Validation may contain user text: avoid printing values or tokens from exception.
        from .common import no_secrets
        message = str(exc)
        try:
            no_secrets(message)
        except OpsError:
            message = "Erro com possível segredo na mensagem; detalhes omitidos."
        print(encode({"state": "ERROR", "message": message}), file=sys.stderr)
        return 2
    finally:
        if ops:
            ops.store.close()
