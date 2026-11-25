#pragma once
#include <SDL3/SDL.h>
#include <vulkan/vulkan.h>
#include <algorithm>
#include <cstddef>
#include <cstring>
#include <stdexcept>
#include <string>
#include <vector>
#include "text.hpp"
#ifdef __XSDK__
#include "shaders_bundle.h"
#else
#include <SDL3/SDL_vulkan.h>
#include "solid_vert.h"
#include "solid_frag.h"
#endif

inline void check(VkResult result, const char* operation) {
    if (result != VK_SUCCESS)
        throw std::runtime_error(std::string(operation) + " failed: " + std::to_string(int(result)));
}
#define VK_CHECK(call) check((call), #call)

class Graphics {
    SDL_Window* window = nullptr;
    VkInstance instance{};
    VkSurfaceKHR surface{};
    VkPhysicalDevice physical{};
    VkDevice device{};
    VkQueue queue{};
    VkSwapchainKHR swapchain{};
    VkExtent2D extent{};
    VkRenderPass pass{};
    VkPipelineLayout layout{};
    VkPipeline pipeline{};
    VkCommandPool pool{};
    VkCommandBuffer command{};
    VkFence fence{};
    VkSemaphore acquired{};
    std::vector<VkSemaphore> rendered;
    std::vector<VkImageView> views;
    std::vector<VkFramebuffer> frames;
    VkBuffer buffer{};
    VkDeviceMemory memory{};
    void* mapped = nullptr;
    static constexpr size_t capacity = 65536 * sizeof(Vertex);

    VkShaderModule shader(const uint32_t* data, size_t bytes) {
        VkShaderModuleCreateInfo info{VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO};
        info.codeSize = bytes; info.pCode = data;
        VkShaderModule module{};
        VK_CHECK(vkCreateShaderModule(device, &info, nullptr, &module));
        return module;
    }

public:
    void init() {
        VkApplicationInfo app{VK_STRUCTURE_TYPE_APPLICATION_INFO};
        app.pApplicationName = "Revive360 Hello"; app.apiVersion = VK_API_VERSION_1_0;
        VkInstanceCreateInfo info{VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO}; info.pApplicationInfo = &app;
#ifdef __XSDK__
        const char* extensions[] = {VK_KHR_SURFACE_EXTENSION_NAME, VK_KHR_DISPLAY_EXTENSION_NAME};
        info.enabledExtensionCount = 2; info.ppEnabledExtensionNames = extensions;
#else
        window = SDL_CreateWindow(app.pApplicationName, 1280, 720, SDL_WINDOW_VULKAN);
        if (!window) throw std::runtime_error(SDL_GetError());
        Uint32 count;
        info.ppEnabledExtensionNames = SDL_Vulkan_GetInstanceExtensions(&count);
        info.enabledExtensionCount = count;
#endif
        VK_CHECK(vkCreateInstance(&info, nullptr, &instance));
        uint32_t countDevices = 0;
        VK_CHECK(vkEnumeratePhysicalDevices(instance, &countDevices, nullptr));
        if (!countDevices) throw std::runtime_error("No Vulkan device");
        std::vector<VkPhysicalDevice> devices(countDevices);
        VK_CHECK(vkEnumeratePhysicalDevices(instance, &countDevices, devices.data()));
#ifdef __XSDK__
        physical = devices[0];
        uint32_t count = 1;
        VkDisplayPropertiesKHR display{};
        VK_CHECK(vkGetPhysicalDeviceDisplayPropertiesKHR(physical, &count, &display));
        if (!count) throw std::runtime_error("No console display");
        count = 1; VkDisplayModePropertiesKHR mode{};
        VK_CHECK(vkGetDisplayModePropertiesKHR(physical, display.display, &count, &mode));
        if (!count) throw std::runtime_error("No console display mode");
        VkDisplaySurfaceCreateInfoKHR displayInfo{VK_STRUCTURE_TYPE_DISPLAY_SURFACE_CREATE_INFO_KHR};
        displayInfo.displayMode = mode.displayMode;
        displayInfo.transform = VK_SURFACE_TRANSFORM_IDENTITY_BIT_KHR;
        displayInfo.alphaMode = VK_DISPLAY_PLANE_ALPHA_OPAQUE_BIT_KHR;
        displayInfo.imageExtent = mode.parameters.visibleRegion;
        VK_CHECK(vkCreateDisplayPlaneSurfaceKHR(instance, &displayInfo, nullptr, &surface));
#else
        if (!SDL_Vulkan_CreateSurface(window, instance, nullptr, &surface))
            throw std::runtime_error(SDL_GetError());
#endif
        uint32_t family = UINT32_MAX;
        for (auto candidate : devices) {
            uint32_t n = 0;
            vkGetPhysicalDeviceQueueFamilyProperties(candidate, &n, nullptr);
            std::vector<VkQueueFamilyProperties> families(n);
            vkGetPhysicalDeviceQueueFamilyProperties(candidate, &n, families.data());
            for (uint32_t i = 0; i < n; ++i) {
                VkBool32 present = false;
                VK_CHECK(vkGetPhysicalDeviceSurfaceSupportKHR(candidate, i, surface, &present));
                if ((families[i].queueFlags & VK_QUEUE_GRAPHICS_BIT) && present) {
                    physical = candidate; family = i; break;
                }
            }
            if (family != UINT32_MAX) break;
        }
        if (family == UINT32_MAX) throw std::runtime_error("No graphics/present queue");
        float priority = 1;
        VkDeviceQueueCreateInfo queueInfo{VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO};
        queueInfo.queueFamilyIndex = family; queueInfo.queueCount = 1; queueInfo.pQueuePriorities = &priority;
        const char* extension = VK_KHR_SWAPCHAIN_EXTENSION_NAME;
        VkDeviceCreateInfo deviceInfo{VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO};
        deviceInfo.queueCreateInfoCount = 1; deviceInfo.pQueueCreateInfos = &queueInfo;
        deviceInfo.enabledExtensionCount = 1; deviceInfo.ppEnabledExtensionNames = &extension;
        VK_CHECK(vkCreateDevice(physical, &deviceInfo, nullptr, &device));
        vkGetDeviceQueue(device, family, 0, &queue);

        VkSurfaceCapabilitiesKHR caps{};
        VK_CHECK(vkGetPhysicalDeviceSurfaceCapabilitiesKHR(physical, surface, &caps));
        extent = caps.currentExtent;
        if (extent.width == UINT32_MAX)
            extent = {std::clamp(1280u, caps.minImageExtent.width, caps.maxImageExtent.width),
                      std::clamp(720u, caps.minImageExtent.height, caps.maxImageExtent.height)};
        uint32_t n = 0;
        VK_CHECK(vkGetPhysicalDeviceSurfaceFormatsKHR(physical, surface, &n, nullptr));
        if (!n) throw std::runtime_error("No surface format");
        std::vector<VkSurfaceFormatKHR> formats(n);
        VK_CHECK(vkGetPhysicalDeviceSurfaceFormatsKHR(physical, surface, &n, formats.data()));
        auto format = formats[0];
        for (auto f : formats) if (f.format == VK_FORMAT_B8G8R8A8_UNORM) format = f;
        if (format.format == VK_FORMAT_UNDEFINED) format.format = VK_FORMAT_B8G8R8A8_UNORM;
        VkSwapchainCreateInfoKHR swapInfo{VK_STRUCTURE_TYPE_SWAPCHAIN_CREATE_INFO_KHR};
        swapInfo.surface = surface; swapInfo.minImageCount = std::max(2u, caps.minImageCount);
        if (caps.maxImageCount) swapInfo.minImageCount = std::min(swapInfo.minImageCount, caps.maxImageCount);
        swapInfo.imageFormat = format.format; swapInfo.imageColorSpace = format.colorSpace;
        swapInfo.imageExtent = extent; swapInfo.imageArrayLayers = 1;
        swapInfo.imageUsage = VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT;
        swapInfo.preTransform = caps.currentTransform;
        for (auto alpha : {VK_COMPOSITE_ALPHA_OPAQUE_BIT_KHR, VK_COMPOSITE_ALPHA_PRE_MULTIPLIED_BIT_KHR,
                           VK_COMPOSITE_ALPHA_POST_MULTIPLIED_BIT_KHR, VK_COMPOSITE_ALPHA_INHERIT_BIT_KHR})
            if (caps.supportedCompositeAlpha & alpha) { swapInfo.compositeAlpha = alpha; break; }
        swapInfo.presentMode = VK_PRESENT_MODE_FIFO_KHR; swapInfo.clipped = true;
        VK_CHECK(vkCreateSwapchainKHR(device, &swapInfo, nullptr, &swapchain));
        VK_CHECK(vkGetSwapchainImagesKHR(device, swapchain, &n, nullptr));
        std::vector<VkImage> images(n);
        VK_CHECK(vkGetSwapchainImagesKHR(device, swapchain, &n, images.data()));
        VkAttachmentDescription attachment{};
        attachment.format = format.format; attachment.samples = VK_SAMPLE_COUNT_1_BIT;
        attachment.loadOp = VK_ATTACHMENT_LOAD_OP_CLEAR; attachment.storeOp = VK_ATTACHMENT_STORE_OP_STORE;
        attachment.stencilLoadOp = VK_ATTACHMENT_LOAD_OP_DONT_CARE;
        attachment.stencilStoreOp = VK_ATTACHMENT_STORE_OP_DONT_CARE;
        attachment.initialLayout = VK_IMAGE_LAYOUT_UNDEFINED;
        attachment.finalLayout = VK_IMAGE_LAYOUT_PRESENT_SRC_KHR;
        VkAttachmentReference reference{0, VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL};
        VkSubpassDescription subpass{}; subpass.pipelineBindPoint = VK_PIPELINE_BIND_POINT_GRAPHICS;
        subpass.colorAttachmentCount = 1; subpass.pColorAttachments = &reference;
        VkSubpassDependency dependency{};
        dependency.srcSubpass = VK_SUBPASS_EXTERNAL; dependency.dstSubpass = 0;
        dependency.srcStageMask = dependency.dstStageMask = VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT;
        dependency.dstAccessMask = VK_ACCESS_COLOR_ATTACHMENT_WRITE_BIT;
        VkRenderPassCreateInfo passInfo{VK_STRUCTURE_TYPE_RENDER_PASS_CREATE_INFO};
        passInfo.attachmentCount = 1; passInfo.pAttachments = &attachment;
        passInfo.subpassCount = 1; passInfo.pSubpasses = &subpass;
        passInfo.dependencyCount = 1; passInfo.pDependencies = &dependency;
        VK_CHECK(vkCreateRenderPass(device, &passInfo, nullptr, &pass));
        views.resize(n); frames.resize(n); rendered.resize(n);
        for (uint32_t i = 0; i < n; ++i) {
            VkImageViewCreateInfo viewInfo{VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO};
            viewInfo.image = images[i]; viewInfo.viewType = VK_IMAGE_VIEW_TYPE_2D;
            viewInfo.format = format.format;
            viewInfo.subresourceRange = {VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1};
            VK_CHECK(vkCreateImageView(device, &viewInfo, nullptr, &views[i]));
            VkFramebufferCreateInfo frameInfo{VK_STRUCTURE_TYPE_FRAMEBUFFER_CREATE_INFO};
            frameInfo.renderPass = pass; frameInfo.attachmentCount = 1; frameInfo.pAttachments = &views[i];
            frameInfo.width = extent.width; frameInfo.height = extent.height; frameInfo.layers = 1;
            VK_CHECK(vkCreateFramebuffer(device, &frameInfo, nullptr, &frames[i]));
            VkSemaphoreCreateInfo semaphoreInfo{VK_STRUCTURE_TYPE_SEMAPHORE_CREATE_INFO};
            VK_CHECK(vkCreateSemaphore(device, &semaphoreInfo, nullptr, &rendered[i]));
        }

        VkPipelineLayoutCreateInfo layoutInfo{VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO};
        VK_CHECK(vkCreatePipelineLayout(device, &layoutInfo, nullptr, &layout));
#ifdef __XSDK__
        auto vs = shader(solid_vert_spirv, SOLID_VERT_SPIRV_BYTES);
        auto fs = shader(solid_frag_spirv, SOLID_FRAG_SPIRV_BYTES);
#else
        auto vs = shader(solid_vert_spirv, sizeof solid_vert_spirv);
        auto fs = shader(solid_frag_spirv, sizeof solid_frag_spirv);
#endif
        VkPipelineShaderStageCreateInfo stages[2]{};
        stages[0].sType = stages[1].sType = VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO;
        stages[0].stage = VK_SHADER_STAGE_VERTEX_BIT; stages[0].module = vs; stages[0].pName = "main";
        stages[1].stage = VK_SHADER_STAGE_FRAGMENT_BIT; stages[1].module = fs; stages[1].pName = "main";
        VkVertexInputBindingDescription binding{0, sizeof(Vertex), VK_VERTEX_INPUT_RATE_VERTEX};
        VkVertexInputAttributeDescription attributes[] = {
            {0, 0, VK_FORMAT_R32G32_SFLOAT, 0}, {1, 0, VK_FORMAT_R32G32B32A32_SFLOAT, offsetof(Vertex,r)}};
        VkPipelineVertexInputStateCreateInfo vertexInfo{VK_STRUCTURE_TYPE_PIPELINE_VERTEX_INPUT_STATE_CREATE_INFO};
        vertexInfo.vertexBindingDescriptionCount = 1; vertexInfo.pVertexBindingDescriptions = &binding;
        vertexInfo.vertexAttributeDescriptionCount = 2; vertexInfo.pVertexAttributeDescriptions = attributes;
        VkPipelineInputAssemblyStateCreateInfo assembly{VK_STRUCTURE_TYPE_PIPELINE_INPUT_ASSEMBLY_STATE_CREATE_INFO};
        assembly.topology = VK_PRIMITIVE_TOPOLOGY_TRIANGLE_LIST;
        VkViewport viewport{0, 0, float(extent.width), float(extent.height), 0, 1};
        VkRect2D scissor{{0,0}, extent};
        VkPipelineViewportStateCreateInfo viewportInfo{VK_STRUCTURE_TYPE_PIPELINE_VIEWPORT_STATE_CREATE_INFO};
        viewportInfo.viewportCount = 1; viewportInfo.pViewports = &viewport;
        viewportInfo.scissorCount = 1; viewportInfo.pScissors = &scissor;
        VkPipelineRasterizationStateCreateInfo raster{VK_STRUCTURE_TYPE_PIPELINE_RASTERIZATION_STATE_CREATE_INFO};
        raster.polygonMode = VK_POLYGON_MODE_FILL; raster.cullMode = VK_CULL_MODE_NONE; raster.lineWidth = 1;
        VkPipelineMultisampleStateCreateInfo samples{VK_STRUCTURE_TYPE_PIPELINE_MULTISAMPLE_STATE_CREATE_INFO};
        samples.rasterizationSamples = VK_SAMPLE_COUNT_1_BIT;
        VkPipelineDepthStencilStateCreateInfo depth{VK_STRUCTURE_TYPE_PIPELINE_DEPTH_STENCIL_STATE_CREATE_INFO};
        VkPipelineColorBlendAttachmentState blend{}; blend.colorWriteMask = 15;
        VkPipelineColorBlendStateCreateInfo blendInfo{VK_STRUCTURE_TYPE_PIPELINE_COLOR_BLEND_STATE_CREATE_INFO};
        blendInfo.attachmentCount = 1; blendInfo.pAttachments = &blend;
        VkGraphicsPipelineCreateInfo pipelineInfo{VK_STRUCTURE_TYPE_GRAPHICS_PIPELINE_CREATE_INFO};
        pipelineInfo.stageCount = 2; pipelineInfo.pStages = stages;
        pipelineInfo.pVertexInputState = &vertexInfo; pipelineInfo.pInputAssemblyState = &assembly;
        pipelineInfo.pViewportState = &viewportInfo; pipelineInfo.pRasterizationState = &raster;
        pipelineInfo.pMultisampleState = &samples; pipelineInfo.pDepthStencilState = &depth;
        pipelineInfo.pColorBlendState = &blendInfo; pipelineInfo.layout = layout; pipelineInfo.renderPass = pass;
        VkResult result = vkCreateGraphicsPipelines(device, VK_NULL_HANDLE, 1, &pipelineInfo, nullptr, &pipeline);
        vkDestroyShaderModule(device, vs, nullptr); vkDestroyShaderModule(device, fs, nullptr);
        check(result, "graphics pipeline");

        VkBufferCreateInfo bufferInfo{VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO};
        bufferInfo.size = capacity; bufferInfo.usage = VK_BUFFER_USAGE_VERTEX_BUFFER_BIT;
        VK_CHECK(vkCreateBuffer(device, &bufferInfo, nullptr, &buffer));
        VkMemoryRequirements requirements{}; vkGetBufferMemoryRequirements(device, buffer, &requirements);
        VkPhysicalDeviceMemoryProperties properties{}; vkGetPhysicalDeviceMemoryProperties(physical, &properties);
        uint32_t type = UINT32_MAX;
        const auto flags = VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT;
        for (uint32_t i = 0; i < properties.memoryTypeCount; ++i)
            if ((requirements.memoryTypeBits & (1u << i)) && (properties.memoryTypes[i].propertyFlags & flags) == flags) { type = i; break; }
        if (type == UINT32_MAX) throw std::runtime_error("No coherent vertex memory");
        VkMemoryAllocateInfo allocation{VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO};
        allocation.allocationSize = requirements.size; allocation.memoryTypeIndex = type;
        VK_CHECK(vkAllocateMemory(device, &allocation, nullptr, &memory));
        VK_CHECK(vkBindBufferMemory(device, buffer, memory, 0));
        VK_CHECK(vkMapMemory(device, memory, 0, capacity, 0, &mapped));
        VkCommandPoolCreateInfo poolInfo{VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO};
        poolInfo.queueFamilyIndex = family; poolInfo.flags = VK_COMMAND_POOL_CREATE_RESET_COMMAND_BUFFER_BIT;
        VK_CHECK(vkCreateCommandPool(device, &poolInfo, nullptr, &pool));
        VkCommandBufferAllocateInfo commandInfo{VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO};
        commandInfo.commandPool = pool; commandInfo.commandBufferCount = 1;
        commandInfo.level = VK_COMMAND_BUFFER_LEVEL_PRIMARY;
        VK_CHECK(vkAllocateCommandBuffers(device, &commandInfo, &command));
        VkFenceCreateInfo fenceInfo{VK_STRUCTURE_TYPE_FENCE_CREATE_INFO}; fenceInfo.flags = VK_FENCE_CREATE_SIGNALED_BIT;
        VK_CHECK(vkCreateFence(device, &fenceInfo, nullptr, &fence));
        VkSemaphoreCreateInfo semaphoreInfo{VK_STRUCTURE_TYPE_SEMAPHORE_CREATE_INFO};
        VK_CHECK(vkCreateSemaphore(device, &semaphoreInfo, nullptr, &acquired));
    }

    void draw(const std::vector<Vertex>& vertices) {
        if (vertices.size() * sizeof(Vertex) > capacity) throw std::runtime_error("Text exceeds vertex capacity");
        VK_CHECK(vkWaitForFences(device, 1, &fence, true, UINT64_MAX));
        uint32_t image;
        auto acquiredResult = vkAcquireNextImageKHR(device, swapchain, UINT64_MAX, acquired, VK_NULL_HANDLE, &image);
        if (acquiredResult != VK_SUCCESS && acquiredResult != VK_SUBOPTIMAL_KHR)
            throw std::runtime_error("Surface changed; restart this fixed-window example");
        std::memcpy(mapped, vertices.data(), vertices.size() * sizeof(Vertex));
        VK_CHECK(vkResetCommandBuffer(command, 0));
        VkCommandBufferBeginInfo begin{VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO};
        begin.flags = VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT;
        VK_CHECK(vkBeginCommandBuffer(command, &begin));
        VkClearValue clear{}; clear.color = {{.025f, .045f, .065f, 1.f}};
        VkRenderPassBeginInfo render{VK_STRUCTURE_TYPE_RENDER_PASS_BEGIN_INFO};
        render.renderPass = pass; render.framebuffer = frames[image]; render.renderArea = {{0,0}, extent};
        render.clearValueCount = 1; render.pClearValues = &clear;
        vkCmdBeginRenderPass(command, &render, VK_SUBPASS_CONTENTS_INLINE);
        vkCmdBindPipeline(command, VK_PIPELINE_BIND_POINT_GRAPHICS, pipeline);
        VkDeviceSize offset = 0;
        vkCmdBindVertexBuffers(command, 0, 1, &buffer, &offset);
        vkCmdDraw(command, static_cast<uint32_t>(vertices.size()), 1, 0, 0);
        vkCmdEndRenderPass(command); VK_CHECK(vkEndCommandBuffer(command));
        VkPipelineStageFlags wait = VK_PIPELINE_STAGE_COLOR_ATTACHMENT_OUTPUT_BIT;
        VkSubmitInfo submit{VK_STRUCTURE_TYPE_SUBMIT_INFO};
        submit.waitSemaphoreCount = 1; submit.pWaitSemaphores = &acquired; submit.pWaitDstStageMask = &wait;
        submit.commandBufferCount = 1; submit.pCommandBuffers = &command;
        submit.signalSemaphoreCount = 1; submit.pSignalSemaphores = &rendered[image];
        VK_CHECK(vkResetFences(device, 1, &fence));
        VK_CHECK(vkQueueSubmit(queue, 1, &submit, fence));
        VkPresentInfoKHR present{VK_STRUCTURE_TYPE_PRESENT_INFO_KHR};
        present.waitSemaphoreCount = 1; present.pWaitSemaphores = &rendered[image];
        present.swapchainCount = 1; present.pSwapchains = &swapchain; present.pImageIndices = &image;
        auto result = vkQueuePresentKHR(queue, &present);
        if (result != VK_SUCCESS && result != VK_SUBOPTIMAL_KHR) check(result, "present");
    }

    ~Graphics() {
        if (device) {
            vkDeviceWaitIdle(device);
            if (mapped) vkUnmapMemory(device, memory);
            if (buffer) vkDestroyBuffer(device, buffer, nullptr);
            if (memory) vkFreeMemory(device, memory, nullptr);
            if (fence) vkDestroyFence(device, fence, nullptr);
            if (acquired) vkDestroySemaphore(device, acquired, nullptr);
            for (auto semaphore : rendered) if (semaphore) vkDestroySemaphore(device, semaphore, nullptr);
            if (pool) vkDestroyCommandPool(device, pool, nullptr);
            if (pipeline) vkDestroyPipeline(device, pipeline, nullptr);
            if (layout) vkDestroyPipelineLayout(device, layout, nullptr);
            for (auto frame : frames) if (frame) vkDestroyFramebuffer(device, frame, nullptr);
            for (auto view : views) if (view) vkDestroyImageView(device, view, nullptr);
            if (pass) vkDestroyRenderPass(device, pass, nullptr);
            if (swapchain) vkDestroySwapchainKHR(device, swapchain, nullptr);
            vkDestroyDevice(device, nullptr);
        }
        if (surface) vkDestroySurfaceKHR(instance, surface, nullptr);
        if (instance) vkDestroyInstance(instance, nullptr);
        if (window) SDL_DestroyWindow(window);
    }
};
