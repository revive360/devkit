// Runs the real template with SDL's real virtual gamepad. No console access.
#define main template_main
#include "../template/src/main.cpp"
#undef main

struct InputState { SDL_Joystick* joystick = nullptr; Uint64 began = 0; int phase = 0; };
static void SDLCALL update(void* userdata) {
    auto& state = *static_cast<InputState*>(userdata);
    const auto elapsed = SDL_GetTicks() - state.began;
    if (!state.joystick) return;
    // SDL calls Update on the polling thread; send real virtual device state.
    if (state.phase == 0 && elapsed > 200) {
        SDL_SetJoystickVirtualButton(state.joystick, SDL_GAMEPAD_BUTTON_SOUTH, true); state.phase = 1;
    } else if (state.phase == 1 && elapsed > 300) {
        SDL_SetJoystickVirtualButton(state.joystick, SDL_GAMEPAD_BUTTON_SOUTH, false); state.phase = 2;
    } else if (state.phase == 2 && elapsed > 400) {
        SDL_SetJoystickVirtualButton(state.joystick, SDL_GAMEPAD_BUTTON_EAST, true); state.phase = 3;
    }
}

int main() {
    if (!SDL_Init(SDL_INIT_GAMEPAD)) return 1;
    SDL_SetHint(SDL_HINT_JOYSTICK_ALLOW_BACKGROUND_EVENTS, "1");
    InputState state;
    SDL_VirtualJoystickDesc description{}; SDL_INIT_INTERFACE(&description);
    description.type = SDL_JOYSTICK_TYPE_GAMEPAD;
    description.nbuttons = 2; description.button_mask = 3;
    description.name = "Revive360 loopback input";
    description.userdata = &state; description.Update = update;
    auto id = SDL_AttachVirtualJoystick(&description);
    state.joystick = SDL_OpenJoystick(id); state.began = SDL_GetTicks();
    if (!state.joystick) return 2;
    char program[] = "hello", option[] = "--frames", count[] = "1000000";
    char* args[] = {program, option, count};
    int result = template_main(3, args);
    // template_main calls SDL_Quit, which also releases the virtual device.
    return result == 0 && state.phase == 3 ? 0 : 3;
}
