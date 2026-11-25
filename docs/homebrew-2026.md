# Como fazer um app homebrew de 360 em 2026

Este é o caminho usado aqui, não uma lista de todos os SDKs existentes. Desenvolvemos apps novos e abertos sobre o ecossistema existente. Não há dependência do SDK da Microsoft e não são distribuídos jogos, chaves nem exploits. BadUpdate/RGH e a configuração do monitor XBDM ficam inteiramente com o usuário, fora da org.

## Preparar o PC

Use Linux. WSL pode servir para compilar; para alcançar o console/receptor UDP, confira a rede e o encaminhamento do seu ambiente. A prova deste devkit foi em Fedora x86_64; não foi uma instalação nova de cada distribuição. Instale Git, CMake 3.25+, Make, Python 3.12+, compiladores C/C++, `glslangValidator` do glslang e, para PC, os arquivos de desenvolvimento SDL3 3.2+, Vulkan e um driver Vulkan (Mesa por software serve para smoke tests).

Para construir a toolchain, xsdk também lista `curl`, `tar`, `xz`, `patch`, bison, flex, texinfo e headers de GMP, MPFR e MPC. Os nomes dos pacotes mudam por distribuição; consulte a [lista do xsdk fixado](https://github.com/xenosworks/xsdk/blob/8c58c7a3fb37bb261c5a11a8a1f4fa8a8bfd0d28/docs/GETTING_STARTED.md). Reserve vários GB e tempo para GCC/newlib. Não sobrescreva uma toolchain de outro projeto.

```sh
# Instala só sob este checkout, salvo se XSDK_TOOLCHAIN tiver outro prefixo.
scripts/bootstrap.sh --toolchain
# Se já possui uma toolchain xsdk compatível:
export XSDK_TOOLCHAIN=/caminho/absoluto/xsdk-gcc
scripts/bootstrap.sh
```

O bootstrap baixa arquivos de revisões fixadas e verifica SHA-256, monta `libxsdk.a`, `libxsc.so` do compilador de shaders no host, `libvulkan4xenon.a` e `libSDL3.a`. Todos os builds usam dois jobs. Não usa a instalação de Microsoft XDK/GDK, nem procura configuração privada do Tube360. Para atualizar, revise o código/licença upstream e troque pins/hashes deliberadamente. Se já houver `.deps` de outro pin, mova essa pasta antes de refazer. Não misture objetos e bibliotecas feitos com convenções de chamada diferentes.

## Um app só, dois alvos

`scripts/build.sh pc` compila shaders GLSL para SPIR-V e usa SDL/Vulkan do host. `scripts/build.sh xbox` compila os mesmos shaders com o xost do xsdk para Xenos, liga o mesmo `main.cpp` às bibliotecas do console e usa o empacotador ELF→XEX aberto do xsdk. No 360, SDL cuida de eventos, controles e timers; a saída de vídeo é `VK_KHR_display` do vulkan4xenon. Não espere que `SDL_CreateRenderer` seja um driver Vulkan do 360.

O template escolhe um formato e tamanho suportados pela superfície, FIFO e uma amostra por pixel. Apresenta texto sólido por um vertex buffer mapeado coerente, com cerca antes de reescrever. Usa um quadro em voo para manter o exemplo pequeno. Para um app mais pesado, siga [desempenho](performance.md) e mantenha buffers separados por quadro. Também aplique a cautela do [bug int64](compiler.md).

## Enviar, observar e depurar

Instale o cliente [XBDM](xbdm.md), descubra o IP numa sub-rede explícita e crie uma pasta dedicada em `HDD:\Apps\`. `put` envia um arquivo por vez; `run` inclui o diretório certo para caminhos relativos. Saia por B antes de substituir o XEX. Não sonda com linhas vazias, não abre debugger e não reinicia o console.

Prefira log UDP: configure `net_log.txt`, inicie o receptor no PC, lance o app e procure startup, primeiro quadro, heartbeat e saída por B. O log em disco pode perder as últimas linhas em desligamento abrupto. Faça uma captura apenas fora da medição; xsdk e o monitor podem discordar do tamanho real, então compare com a TV.

Se o app cair antes do primeiro quadro, separe: inicialização SDL, criação da superfície/dispositivo, compilação offline de shader e ligação. Se `run` parecer não fazer nada, confirme que o título anterior saiu e que o diretório foi enviado. Se o XBDM morrer com o app, pare as tentativas e peça intervenção a quem está com o console. Um reboot não restaura o ambiente de BadUpdate.

## Empacotar e lançar

`scripts/package.py` exige uma árvore limpa e um build associado ao mesmo commit. Inclui XEX, MIT, avisos xsdk/libxenon/Xenia, vulkan4xenon/Khronos, SDL, newlib e GCC Runtime Exception, lock de fontes e fonte do devkit. Não inclui IP, `net_log.txt`, arquivos de conta, ferramentas de destrava ou compilador. Revise o inventário antes de distribuir.

Cada projeto decide sua licença, preservando a compatibilidade das dependências. O uso de IA é permitido, mas a pessoa responde pelo código. Registre o hash do pacote, commit e resultado **em console real** antes de chamá-lo de lançamento. O binário exato da R1 recebeu [aceite físico em 2026-11-25](console-test.md), em um Xbox 360 E (Corona). Apps derivados, outros modelos e builds futuros continuam exigindo seu próprio teste.

## Leituras upstream

- [xsdk: primeiros passos](https://github.com/xenosworks/xsdk/blob/8c58c7a3fb37bb261c5a11a8a1f4fa8a8bfd0d28/docs/GETTING_STARTED.md), [armadilhas](https://github.com/xenosworks/xsdk/blob/8c58c7a3fb37bb261c5a11a8a1f4fa8a8bfd0d28/docs/PITFALLS.md).
- [vulkan4xenon: suporte](https://github.com/xenosworks/vulkan4xenon/blob/df25dc50e6296d89822626b433f4080db05bccc8/docs/SUPPORT.md).
- [SDL-xenon: backend xsdk](https://github.com/xenosworks/SDL-xenon/blob/adb87a744ae056f1849718770cf198fa6c4899f9/docs/README-xsdk.md).

Xbox e Xbox 360 são marcas da Microsoft. A Revive360 não tem vínculo ou endosso dela.
