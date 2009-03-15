
#include <windows.h>
#include <WtsApi32.h>
#include <string>

#pragma comment (lib, "WtsApi32.lib")

struct LOADINFO
{
    DWORD mVersion;
    HWND mHwnd;
    BOOL mKeep;
};

const UINT WM_MCOMMAND = WM_USER + 200,
    WM_MEVALUATE = WM_USER + 201;

const unsigned int CMDMODE_EDITBOX = 1,
    CMDMODE_EDITBOX_PLAINTEXT = 2,
    CMDMODE_FLOOD_PROTECTION = 4;

HWND mirc_hwnd, my_hwnd;
HINSTANCE hinst;

void send_to_mirc(HWND hwnd, const std::string& cmd,
                unsigned int mode = CMDMODE_EDITBOX)
{
    HANDLE handle = CreateFileMappingA(INVALID_HANDLE_VALUE, NULL,
        PAGE_READWRITE, 0, (std::min)(1024u, cmd.size() + 1u), "mIRC999");
    char *data = reinterpret_cast<char*>(MapViewOfFile(handle,
        FILE_MAP_ALL_ACCESS, 0, 0, 0));

    strcpy_s(data, cmd.size() + 1, cmd.c_str());
    SendMessage(hwnd, WM_MCOMMAND, mode, 999);

    UnmapViewOfFile(data);
    CloseHandle(handle);
}

LRESULT WINAPI wnd_proc(HWND hWnd, UINT msg, WPARAM wParam, LPARAM lParam)
{
    if (mirc_hwnd && msg == WM_WTSSESSION_CHANGE)
    {
        if (wParam == WTS_SESSION_LOCK)
        {
            send_to_mirc(mirc_hwnd, "/on_windows_lock");
            return 0;
        }
        else if (wParam == WTS_SESSION_UNLOCK)
        {
            send_to_mirc(mirc_hwnd, "/on_windows_unlock");
            return 0;
        }
    }

    return DefWindowProc(hWnd, msg, wParam, lParam);
}

void __stdcall LoadDll(LOADINFO* t)
{
    t->mKeep = TRUE;
    mirc_hwnd = t->mHwnd;

    WNDCLASSEX wsex;
    wsex.cbSize = sizeof(WNDCLASSEX);
    wsex.hInstance = hinst;
    wsex.style = CS_VREDRAW | CS_HREDRAW;
    wsex.lpfnWndProc = wnd_proc;
    wsex.hbrBackground = reinterpret_cast<HBRUSH>(COLOR_BACKGROUND);
    wsex.hCursor = LoadCursor(0, IDC_ARROW);
    wsex.hIcon = wsex.hIconSm = 0;
    wsex.lpszClassName = L"mirc_lock_notifier";
    wsex.lpszMenuName = 0;
    wsex.cbClsExtra = wsex.cbWndExtra = 0;

    RegisterClassEx(&wsex);

    my_hwnd = CreateWindowEx(0, L"mirc_lock_notifier", L"", WS_POPUP,
        CW_USEDEFAULT, CW_USEDEFAULT, CW_USEDEFAULT, CW_USEDEFAULT, 0,
        0, hinst, 0);

    WTSRegisterSessionNotification(my_hwnd, NOTIFY_FOR_THIS_SESSION);
}

int __stdcall UnloadDll(int mTimeout)
{
    if (mTimeout)
        return 0;

    WTSUnRegisterSessionNotification(my_hwnd);
    DestroyWindow(my_hwnd);

    return 1;
}

int __stdcall Init(HWND, HWND, char*, char*, BOOL, BOOL)
{
    return 0;
}

BOOL WINAPI DllMain(HINSTANCE hinstDLL, DWORD fdwReason, LPVOID)
{
    switch (fdwReason)
    {
        case DLL_PROCESS_ATTACH:
        {
            hinst = hinstDLL;
            break;
        }
    }

    return TRUE;
}
