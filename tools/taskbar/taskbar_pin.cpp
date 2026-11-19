// Minimal official Windows taskbar pin request for the foreground desktop app.
// The only entrypoint is invoked after a user clicks the application's button.
// No Explorer registry writes, shell verbs, policy changes or silent pinning.
#include <windows.h>
#include <winrt/base.h>
#include <winrt/Windows.Foundation.h>
#include <winrt/Windows.UI.Shell.h>

namespace shell = winrt::Windows::UI::Shell;
namespace foundation = winrt::Windows::Foundation;

static bool laf_required() noexcept {
    HKEY key = nullptr;
    constexpr wchar_t path[] =
        L"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\AppModel\\"
        L"LimitedAccessFeatures\\com.microsoft.windows.taskbar.pin";
    if (RegOpenKeyExW(HKEY_LOCAL_MACHINE, path, 0, KEY_QUERY_VALUE, &key) != ERROR_SUCCESS)
        return false;
    DWORD value = 0, type = 0, bytes = sizeof(value);
    constexpr wchar_t seed[] =
        L"4096B239A7295B635C090E647E867B5707DA6AB6CB78340B01FE4E0C8F4953D4";
    const auto rc = RegQueryValueExW(key, seed, nullptr, &type,
                                     reinterpret_cast<BYTE*>(&value), &bytes);
    RegCloseKey(key);
    return rc == ERROR_SUCCESS && type == REG_DWORD && value != 0;
}

extern "C" __declspec(dllexport) int __stdcall WTMMRequestTaskbarPin() noexcept {
    // Return: 0 request started, 1 API unavailable, 2 policy denied,
    // 3 LAF token required, 4 Windows API rejected the request.
    try {
        if (laf_required()) return 3;
        const auto factory = winrt::try_get_activation_factory<
            shell::TaskbarManager, shell::ITaskbarManagerDesktopAppSupportStatics>();
        if (!factory) return 1;
        auto manager = shell::TaskbarManager::GetDefault();
        if (!manager || !manager.IsSupported()) return 1;
        if (!manager.IsPinningAllowed()) return 2;
        // Asynchronously launch the official Windows confirmation UI. Do not
        // block the Qt UI thread or claim pinning succeeded before approval.
        auto operation = manager.RequestPinCurrentAppAsync();
        operation.Completed([](foundation::IAsyncOperation<bool> const&,
                               foundation::AsyncStatus) noexcept {});
        return 0;
    } catch (...) {
        return 4;
    }
}
