# Validação e limites

Preparação inicial em 2026-11-25. O relatório de entrega local contém commits, hashes e caminhos dos logs completos. Nenhum teste abaixo fala com um console real, cria org, faz push ou acessa VPS.

## Repetir as verificações

Na raiz do devkit:

```sh
# Pillow é necessário para o teste de conversão PNG.
PYTHONPATH=src python3 -m unittest discover -s tests -v
scripts/build.sh pc
cmake --build build/pc --target hello-input-check -j2
# Selecionar Lavapipe é opcional; esta é a localização no Fedora da prova.
VK_DRIVER_FILES=/usr/share/vulkan/icd.d/lvp_icd.x86_64.json python3 tests/pc_smoke.py

# Exportar a toolchain previamente preparada. No host compartilhado, usar o lock.
flock ${XDG_RUNTIME_DIR:-/tmp}/revive360-xbox.lock \
  systemd-run --user --scope -q -p MemoryMax=6G -p MemorySwapMax=1G \
  scripts/build.sh xbox
python3 scripts/package.py
```

Os 12 testes Python usam servidores TCP/UDP em `127.0.0.1`: saudação fragmentada, transferência binária, desconexão no meio de download, ordem de bytes do tamanho, CRLF, alias HDD e raiz, diretório de magicboot, erro 413, discovery sem envio de linhas, header de screenshot, bloqueio de injeção/relativos, ausência do comando reboot e sequência UDP. O teste de captura usa um pixel de referência, arquivo truncado e formato não suportado. Isso cobre o contrato observado, não todos os monitores XBDM possíveis.

`tests/pc_smoke.py` roda o aplicativo real, apresenta dez quadros Vulkan offscreen e verifica três mensagens UDP emitidas por ele, incluindo os contadores em ordem de rede. Depois executa a integração com SDL e um gamepad virtual real: A down/up e B encerrando antes do limite de quadros. Não é mock de SDL/Vulkan. Ele não prova a imagem na TV nem que o driver de controle xsdk funcionou no console.

O build Xbox usa as revisões fixadas sem patches privados de Tube360, recompila as três bibliotecas em `.deps`, gera o bundle Xenos e o XEX2. O GCC foi reutilizado da instalação local milestone 52. O scanner upstream relata instruções que Xenia não executa; é um aviso de limite do emulador, não falha do compilador e tampouco uma prova de hardware. O XEX existe e seu hash é registrado; ainda não foi executado.

O empacotador recusa árvore suja, build de outro commit e alteração do binário/lock posterior à prova. O pacote leva inventário com SHA-256 e avisos de runtime. A inspeção de entrega também verifica o inventário ZIP, a equivalência do `source.tar` com o commit e a ausência de `net_log.txt` ou diretórios de build/dependências no fonte. Não há execução de console automatizada no bootstrap/build/package.

## O que ainda falta

- Imagem e legibilidade no Xenos real, A/B em controle físico e retorno ao dashboard mantendo XBDM.
- Log UDP e captura do monitor real neste template; o caminho de captura tem as limitações descritas em [xbdm.md](xbdm.md).
- Uma instalação fria da toolchain inteira: a receita upstream foi auditada e exposta por `--toolchain`, mas a prova reutilizou o GCC local e reconstruiu as bibliotecas.
- Aceite físico e registro de evidências antes de qualquer lançamento. Use [console-test.md](console-test.md).
