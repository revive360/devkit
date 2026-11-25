# Console de verdade, registro na mão

Fecha o ciclo com o binário certo e guarda a prova. Quem tá na frente da TV confere a imagem; o log conta o resto.

**Aceite registrado a partir do relato do coordenador e do dono fornecido no adendo R2.** Este registro não é uma nova execução de console por este agente. O pacote continua de desenvolvimento; aceite físico não cria uma release assinada pelo CI.

## Registro aceito — um console, um modelo

- Data: **2026-11-25**. Responsáveis: coordenador e dono Pedro (`PedroHenrique0713`).
- Console: **Xbox 360 E (Corona)**; ambiente **BadUpdate + Aurora**.
- Fonte do binário: commit `a7696125028f72cf9325c56d89cb05d754b01dc0` (R1).
- XEX SHA-256: `d1071574280ef64b5c3b90f59932666c3614913478754294a0bc13a991598ca5`.
- CLI do devkit: discover, mkdir, put e get; hash de retorno idêntico. Run enviado com o diretório de trabalho.
- UDP observado, conforme relato recebido: `startup`, `first frame submitted`, `gamepad: connected`, heartbeat `frames=302`, A down/up, `B exit`, `normal exit; frames=565`; **exit status 0**.
- O dono confirmou na TV texto legível, sem triângulos. XBDM continuou disponível após sair. Pasta temporária removida pelo coordenador.
- Estado: **`console_validation: accepted`**; registro estruturado em [console-acceptance-2026-11-25.json](console-acceptance-2026-11-25.json).

**Limites:** um console físico e um modelo, no ambiente e hash acima. Não se estende a outros modelos, builds futuros, instalação fria da toolchain, fidelidade de screenshots ou reconexão do controle. Não afirma atestação de CI, publicação ou certificação de catálogo.

`dist/hello/manifest.json`, o manifest dentro de `dist/hello-development.zip` e `build/xbox/build.json` registram o aceite e a data. A atualização é somente de metadados/avisos: XEX, ELF e `source.tar` original permanecem idênticos. O ZIP tem novo hash por incluir o aceite; `dist/SHA256SUMS` foi atualizado. O arquivo fonte da R1 conserva sua documentação histórica. O ZIP anterior está preservado em `.work/evidence/`.

Para reaplicar o relato ao pacote existente, com fonte e hash idênticos, use `python3 scripts/accept_console.py`. A ferramenta não fala com o console, não compila e recusa fonte/hash diferentes; um build novo começa pendente. O roteiro abaixo continua válido para novos testes.

## Preparação e envio

Na raiz do devkit, confira `dist/SHA256SUMS` e `dist/hello/manifest.json`. Confirme commit e hash do XEX. O binário aceito acima tem `console_validation: accepted`; um binário novo deve começar `pending` e obter seu próprio registro. O console deve estar preparado pelo usuário e com XBDM disponível. Não distribua essa preparação, payloads ou chaves.

Instale a CLI e use-a explicitamente. Os endereços abaixo são exemplos; substitua pelos da sua rede:

```sh
python3 -m venv .venv
.venv/bin/pip install -e '.[screenshot]'
export PATH="$PWD/.venv/bin:$PATH"
xbdm discover --network 192.168.1.0/24
xbdm ls 192.168.1.50 'HDD:\'
xbdm mkdir 192.168.1.50 'HDD:\Apps'
xbdm mkdir 192.168.1.50 'HDD:\Apps\Revive360Hello'
xbdm put 192.168.1.50 dist/hello/default.xex 'HDD:\Apps\Revive360Hello\default.xex'
```

Copie também os avisos de licença se for deixar/distribuir a instalação. Para o teste temporário, eles estão preservados no pacote. Faça `get` do XEX enviado para `.work/console-default.xex` e compare com `sha256sum dist/hello/default.xex .work/console-default.xex`; igualdade verifica os bytes, não o funcionamento.

## Log, execução e aceitação

1. Em outro terminal rode `xbdm log --port 7301 --output .work/console-udp.log`. Confira a liberação UDP local. Crie `.work/net_log.txt` contendo o **IP do PC receptor**, um espaço e `7301`, e envie com `xbdm put <console-IP> .work/net_log.txt 'HDD:\Apps\Revive360Hello\net_log.txt'`.
2. Com o título anterior já encerrado, rode `xbdm run <console-IP> 'HDD:\Apps\Revive360Hello\default.xex'`. O cliente envia `magicboot` com `directory` absoluto. Não há reboot.
3. Confirme na TV: fundo escuro, REVIVE360 verde, NEW OPEN SOFTWARE, SDL3 AND VULKAN e instrução de controle. O texto precisa estar legível e sem triângulos aleatórios. Startup e `first frame submitted` devem chegar por UDP. Espere pelo heartbeat de cinco segundos.
4. Pressione A: A PRESSED aparece enquanto o botão está abaixado e some ao soltar; log mostra down/up. Desconecte e reconecte o controle se possível e confirme as mensagens de conexão.
5. Pressione B: o app retorna normalmente ao dashboard, sem reiniciar o console. O log deve conter `B exit` e `normal exit`. Verifique que XBDM continua disponível com `ls` e que o ambiente não precisou ser preparado de novo.
6. Se precisar de captura, faça-a depois da observação visual e fora de qualquer medição: `xbdm shot <console-IP> .work/console-shot`. Leia [as limitações](xbdm.md#captura-de-tela); um dump xsdk parcial não prova um quadro completo.
7. Registre data, responsável, modelo de console, ambiente homebrew, commit, hashes, resultado de cada passo e caminhos dos logs/foto. Falhou algum passo: mantenha o estado pendente e reporte o sintoma. Não publique como lançamento.

Modelo de registro:

```text
Date / tester:
Console model / homebrew environment:
Source commit / package SHA-256 / default.xex SHA-256:
Upload roundtrip hash: PASS / FAIL
Picture and text on TV: PASS / FAIL
UDP startup, first frame, heartbeat: PASS / FAIL
A down/up, reconnect: PASS / FAIL / NOT TESTED
B normal exit, dashboard and XBDM still available: PASS / FAIL
Evidence paths / limitations:
Release acceptance: PENDING / ACCEPTED (only after required steps pass)
```

Depois do teste, a pasta é temporária. Remova-a pelo gerenciador de arquivos do dashboard, com o app encerrado; a CLI não implementa exclusão recursiva. Não deixe cópias confundindo o Aurora. Se travar, não repita lançamentos nem tente reboot remoto: quem está ao lado do console decide a recuperação.
