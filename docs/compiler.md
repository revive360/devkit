# GCC xsdk: comparação de int64 entre 2 e 4 GiB

O Tube360 encontrou uma falha concreta no GCC xsdk usado localmente, GCC 15.3.0 com os patches de milestone 52. Não é um problema do servidor HTTP nem de um `int` pequeno no parser. O Xenon usa registradores de 64 bits com endereços/execução em modo de 32 bits (`MSR.SF=0`). A otimização **RTL combine** pode emitir `mr.` para testar o sinal de um `int64_t`; nesse modo, CR0 reflete os 32 bits baixos em vez do valor de 64 bits esperado.

Um tamanho positivo entre `0x80000000` e `0xffffffff` pode ser tratado como negativo. Na prova do Tube360, `avio_size` devolvia tamanho menos um e não restaurava o cursor, o índice `sidx` parecia incompleto, o demuxer varria fragmentos e seeks grandes falhavam. Isso explica abertura lenta no console que não aparecia no PC.

O workaround é compilar a unidade afetada com:

```text
-fdisable-rtl-combine
```

Isso desliga um passe específico; não desliga todas as otimizações e não corrige objetos já compilados. No Tube360 o ajuste foi aplicado a `libavformat/*.o`, com reconstrução desses objetos, preservando as opções dos kernels de decodificação H.264/VMX. O template aplica a opção ao alvo de aplicação como padrão conservador. Ele **não** recompila todos os runtimes/libs upstream com a opção nem afirma que todo código externo esteja protegido.

Ao importar código de rede/arquivos, teste tamanhos, offsets, timestamps e comparações assinadas de 64 bits. Use valores em torno de 2 GiB e 4 GiB, incluindo exatamente as fronteiras; examine o assembly e execute em PowerPC com `SF=0` ou no console. Um teste x86_64 ou um emulador PowerPC em modo só de 64 bits não reproduz a condição. Não amplie o workaround a todos os kernels por suposição: identifique a unidade e meça o custo.

Evidência original: Tube360, tarefa F46 de 2026-11-25, commits `ba648af` e `f096b34` (histórico de desenvolvimento). Casos sintéticos de cerca de 2,83 GB, 5.400 entradas sidx e seeks em 120/10.000 s falhavam antes e passavam depois na prova PowerPC. A task F48 estendeu a inspeção a consumidores de tamanhos/offsets. Não copiamos o FFmpeg nem seus testes para este kit e não usamos esses resultados como prova de execução deste template no console. O relatório local identifica as evidências originais.

A revisão xsdk fixada ainda não incorpora este workaround em sua receita global. Ao trocar de toolchain, revalide a falha antes de remover a opção; o número da versão GCC sozinho não prova quais patches e passes foram usados.
