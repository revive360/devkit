# Roteiro para o coordenador — pendente

**Nenhum acesso ao console foi realizado na preparação do devkit.** O XEX/ZIP é de desenvolvimento. Só marque aceite depois das verificações abaixo num console real. Não precisa mexer na instalação do Tube360.

## Preparação e envio

Na raiz do devkit, confira `dist/SHA256SUMS` e `dist/hello/manifest.json`. Confirme o commit de fonte, hash do XEX e `console_validation: pending`. O console deve estar preparado pelo usuário e com XBDM disponível. Não distribua essa preparação, payloads ou chaves.

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
