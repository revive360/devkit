# Xenos: mede antes de mexer

Traz os números do 360. Dá pra gastar uma tarde no lugar errado sem medir; começa pelo passe que pesa.

As medidas abaixo vêm do FORCE PUSH, no console de Pedro com BadUpdate em 2026-11-02, usando timestamps Vulkan entre passes (período observado 2 ns). São observações daquela cena, não metas garantidas nem benchmarks deste template. Base: memória de desenvolvimento `reference-xbox360-xenos-desempenho-vulkan4xenon.md`, revisada em 2026-11-04.

| Trabalho medido | Observação | Uso prático |
| --- | --- | --- |
| Cerca de 360 draws | CPU abaixo de 3 ms; shader de cena complexo cerca de 17 ns/pixel | Comece medindo custo por pixel/overdraw, não presumindo gargalo de draw calls. |
| Cena com 4 luzes, sombra, AO e ACES | ~10 ms em 1024×576, ~8,3 ms em 960×540, ~16 ms em 720p | Resolução de render pode pesar mais que geometria. |
| Passe final em 720p | De ~3,3 ms para ~0,7 ms ao trocar gradação por cópia | Evite ALU de tela cheia sem necessidade; ~25 instruções ALU custaram ~2 ms nessa medição. |
| MSAA | 4× em 720p adicionou ~15 ms; 2× em 1024×576 adicionou ~6 ms | Comece com 1×; os 10 MB de eDRAM e o tiling importam. |
| Dois quadros em voo | Cena antes presa em 30 passou a 55–60 fps | Duplique command buffers, cercas, UBOs e buffers de texto; não sobrescreva dados ainda usados pela GPU. |
| Véu de UI com shader complexo | ~3 ms em tela cheia | Use shader sólido quando suficiente. |

FIFO pode transformar um quadro de 17 ms em intervalo de 33 ms. “Espera da GPU” no CPU e contador de FPS não são tempo GPU. Meça com timestamps válidos, fora dos passes com tiling, e compare a imagem na TV. Captura XBDM altera o desempenho.

Na versão usada, o vulkan4xenon recusa sampler de comparação com filtro linear (use `NEAREST`), swapchain incompatível com o formato/tamanho de superfície ou modo diferente de FIFO, e timestamp/query dentro de passe com tiling. Confira [SUPPORT.md upstream](https://github.com/xenosworks/vulkan4xenon/blob/df25dc50e6296d89822626b433f4080db05bccc8/docs/SUPPORT.md) ao projetar a renderização; não suponha a cobertura de um driver Vulkan desktop completo.

Um shader de texto que só amostrava textura no interpolante produziu triângulos sólidos/corrompidos no console, embora o log parecesse bom. O caminho mais complexo da cena dava texto correto; a causa do microcódigo não foi apurada. O template evita esse caminho com glifos de geometria e cor sólida. Isso não prova que todos os shaders de textura estejam quebrados. Otimização só é aceita depois de conferir a imagem real.

O exemplo mantém um quadro em voo, sem MSAA, sem textura, com memória coerente e FIFO. É uma base de leitura fácil, não um renderizador otimizado de produção. Para crescer, meça CPU/GPU separadamente, reduza trabalho por pixel e introduza dois quadros em voo com recursos separados quando a medida justificar.
