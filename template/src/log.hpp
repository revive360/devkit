#pragma once
#include <cstdio>
#ifdef __XSDK__
#include <xsdk/log.h>
#define APP_LOG(...) xsdk_log_write(__VA_ARGS__)
#else
#include <arpa/inet.h>
#include <sys/socket.h>
#include <unistd.h>
#include <cstdarg>
#include <cstdint>
#include <cstring>

// Same framing as xsdk: network-order uint32 sequence followed by UTF-8 text.
class AppLog {
    int fd = -1;
    sockaddr_in destination{};
    uint32_t sequence = 0;
public:
    AppLog() {
        FILE* file = std::fopen("net_log.txt", "r");
        if (!file) return;
        char ip[16]; unsigned port;
        bool valid = std::fscanf(file, "%15s %u", ip, &port) == 2 && port > 0 && port <= 65535;
        std::fclose(file);
        destination.sin_family = AF_INET;
        if (valid && inet_pton(AF_INET, ip, &destination.sin_addr) == 1) {
            destination.sin_port = htons(static_cast<uint16_t>(port));
            fd = socket(AF_INET, SOCK_DGRAM, 0);
        }
    }
    ~AppLog() { if (fd >= 0) close(fd); }
    void write(const char* format, ...) {
        char text[1024];
        va_list args; va_start(args, format);
        std::vsnprintf(text, sizeof text, format, args); va_end(args);
        std::puts(text); std::fflush(stdout);
        if (fd < 0) return;
        unsigned char datagram[4 + sizeof text];
        uint32_t number = htonl(sequence++);
        std::memcpy(datagram, &number, 4);
        size_t length = std::strlen(text);
        std::memcpy(datagram + 4, text, length);
        sendto(fd, datagram, length + 4, 0, reinterpret_cast<sockaddr*>(&destination), sizeof destination);
    }
};
inline AppLog& appLog() { static AppLog log; return log; }
#define APP_LOG(...) appLog().write(__VA_ARGS__)
#endif
