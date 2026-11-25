#include "log.hpp"
#include "graphics.hpp"
#include <cstdlib>

int main(int argc, char** argv) {
    unsigned limit = 0;
    if (argc == 3 && std::string(argv[1]) == "--frames") {
        char* end = nullptr;
        unsigned long parsed = std::strtoul(argv[2], &end, 10);
        if (!*argv[2] || *end || parsed == 0 || parsed > 1000000) return 2;
        limit = static_cast<unsigned>(parsed);
    } else if (argc != 1) {
        APP_LOG("Usage: hello [--frames positive-count]"); return 2;
    }
    const auto flags = SDL_INIT_GAMEPAD | SDL_INIT_EVENTS
#ifndef __XSDK__
        | SDL_INIT_VIDEO
#endif
        ;
    if (!SDL_Init(flags)) { APP_LOG("SDL init failed: %s", SDL_GetError()); return 1; }
    int status = 0;
    std::vector<SDL_Gamepad*> pads;
    APP_LOG("hello: startup; SDL3 and Vulkan; B or Escape exits");
    try {
        Graphics graphics;
        graphics.init();
        auto openPad = [&](SDL_JoystickID id) {
            if (auto* pad = SDL_OpenGamepad(id)) { pads.push_back(pad); APP_LOG("gamepad: connected"); }
        };
        int count = 0;
        SDL_JoystickID* ids = SDL_GetGamepads(&count);
        for (int i = 0; i < count; ++i) openPad(ids[i]);
        SDL_free(ids);
        bool quit = false, pressed = false;
        unsigned frames = 0;
        uint64_t heartbeat = SDL_GetTicks();
        while (!quit && (!limit || frames < limit)) {
            SDL_Event event;
            while (SDL_PollEvent(&event)) {
                if (event.type == SDL_EVENT_QUIT || (event.type == SDL_EVENT_KEY_DOWN && event.key.key == SDLK_ESCAPE)) quit = true;
                if (event.type == SDL_EVENT_GAMEPAD_ADDED) {
                    bool known = false;
                    for (auto* pad : pads) known |= SDL_GetGamepadID(pad) == event.gdevice.which;
                    if (!known) openPad(event.gdevice.which);
                }
                if (event.type == SDL_EVENT_GAMEPAD_REMOVED) {
                    for (auto it = pads.begin(); it != pads.end();) {
                        if (SDL_GetGamepadID(*it) == event.gdevice.which) {
                            SDL_CloseGamepad(*it); it = pads.erase(it); APP_LOG("gamepad: disconnected");
                        } else ++it;
                    }
                    pressed = false;
                }
                if (event.type == SDL_EVENT_GAMEPAD_BUTTON_DOWN || event.type == SDL_EVENT_GAMEPAD_BUTTON_UP) {
                    const bool down = event.type == SDL_EVENT_GAMEPAD_BUTTON_DOWN;
                    APP_LOG("gamepad: button %u %s", unsigned(event.gbutton.button), down ? "down" : "up");
                    if (event.gbutton.button == SDL_GAMEPAD_BUTTON_EAST && down) { APP_LOG("hello: B exit"); quit = true; }
                    if (event.gbutton.button == SDL_GAMEPAD_BUTTON_SOUTH) pressed = down;
                }
            }
            if (quit) break;
            std::vector<Vertex> vertices;
            vertices.reserve(16000);
            text(vertices, "REVIVE360", 110, 120, 13, .3f, .95f, .65f);
            text(vertices, "NEW OPEN SOFTWARE", 110, 280, 5);
            text(vertices, "SDL3 AND VULKAN", 110, 350, 5);
            text(vertices, pads.empty() ? "CONNECT A CONTROLLER" : "A TO TEST - B TO EXIT", 110, 460, 5);
            if (pressed) text(vertices, "A PRESSED", 110, 540, 5, .3f, .95f, .65f);
            graphics.draw(vertices);
            ++frames;
            if (frames == 1) APP_LOG("hello: first frame submitted");
            if (SDL_GetTicks() - heartbeat >= 5000) {
                APP_LOG("hello: heartbeat; frames=%u; pads=%u", frames, unsigned(pads.size()));
                heartbeat = SDL_GetTicks();
            }
        }
        APP_LOG("hello: normal exit; frames=%u", frames);
    } catch (const std::exception& error) {
        APP_LOG("hello: error: %s", error.what()); status = 1;
    }
    for (auto* pad : pads) SDL_CloseGamepad(pad);
    SDL_Quit();
    return status; // xsdk returns to the dashboard; never reboot the console.
}
