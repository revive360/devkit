# Validação e limites

Preparação inicial em 2026-11-25. O relatório de entrega local contém commits, hashes e caminhos dos logs completos. Os testes automatizados locais abaixo não falam com console real, criam org, fazem push ou acessam VPS. O aceite físico posterior, relatado pelo coordenador e pelo dono, está registrado separadamente.

## Aceite físico registrado em 2026-11-25

**`console_validation: accepted`**, por relato do coordenador e do dono: Xbox 360 E (Corona), BadUpdate + Aurora, **um console e um modelo**. [Registro completo](console-test.md) e [evidência estruturada](console-acceptance-2026-11-25.json). Fonte `a7696125028f72cf9325c56d89cb05d754b01dc0`; XEX `d1071574280ef64b5c3b90f59932666c3614913478754294a0bc13a991598ca5`.

Discover/mkdir/put/get com hash idêntico e run com diretório; UDP de startup, primeiro quadro, controle conectado, heartbeat frames=302, A down/up, B exit, normal exit frames=565, exit status 0. O dono confirmou texto legível na TV sem triângulos; XBDM disponível após sair; pasta temporária removida pelo coordenador. O relato não foi repetido por este agente e não cobre builds futuros/outros modelos. O binário continua um artefato de desenvolvimento sem proveniência de release do CI.

Os manifests local e do ZIP foram atualizados com data e escopo. XEX/ELF/fonte originais foram preservados; só o ZIP, seus avisos e metadados mudaram. O empacotamento normal de um **novo build** continua começando com validação pendente; nunca herda automaticamente este aceite.

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

O build Xbox usa as revisões fixadas sem patches privados de Tube360, recompila as três bibliotecas em `.deps`, gera o bundle Xenos e o XEX2. O GCC foi reutilizado da instalação local milestone 52. O scanner upstream relata instruções que Xenia não executa; é um aviso de limite do emulador, não falha do compilador e tampouco uma prova de hardware. O XEX desse hash foi executado no aceite físico relatado acima; a inspeção de build/emulador, isoladamente, continua sem provar hardware.

O empacotador recusa árvore suja, build de outro commit e alteração do binário/lock posterior à prova. O pacote leva inventário com SHA-256 e avisos de runtime. A inspeção de entrega também verifica o inventário ZIP, a equivalência do `source.tar` com o commit e a ausência de `net_log.txt` ou diretórios de build/dependências no fonte. Não há execução de console automatizada no bootstrap/build/package.

Os registros JSON não incluem caminhos privados de host. O XEX ainda pode conter strings de caminhos de fonte da instalação GCC/newlib reutilizada (asserts internos); isso foi observado na inspeção binária. Não são arquivos de configuração ou credenciais. Uma distribuição que exija remover esses caminhos precisa reconstruir os runtimes com prefix mapping, e revalidar o binário resultante.

## O que ainda falta

- Cobertura de outros consoles/modelos/ambientes. Imagem, legibilidade, A/B físicos e retorno mantendo XBDM já foram aceitos no console registrado.
- Validar fidelidade de captura do monitor real; [xbdm.md](xbdm.md) descreve limitações. O UDP de execução foi confirmado pelo relato, sem afirmar uma screenshot completa.
- Uma instalação fria da toolchain inteira: a receita upstream foi auditada e exposta por `--toolchain`, mas a prova reutilizou o GCC local e reconstruiu as bibliotecas.
- Testar cada futuro binário exato antes de lançamento e implementar os gates de CI/assinatura. O aceite deste hash já está em [console-test.md](console-test.md).
