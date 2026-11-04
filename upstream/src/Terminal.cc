// Modified for the unofficial Windows port, 2026-11-04; see ../README.md and windows-port.patch.
/*
 * steghide 0.5.1 - a steganography program
 * Copyright (C) 1999-2003 Stefan Hetzl <shetzl@chello.at>
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
 *
 */

#include <unistd.h>
#ifdef _WIN32
#include <windows.h>
#endif

#include "Terminal.h"
#include "common.h"
#include "error.h"

#ifdef HAVE_TERMIOS_H
Terminal::Terminal() {
    if ((tcgetattr(STDIN_FILENO, &InitAttr)) != 0) {
        throw SteghideError(_("could not get terminal attributes."));
    }
}

void Terminal::EchoOff() {
    struct termios curattr;
    if ((tcgetattr(STDIN_FILENO, &curattr)) != 0) {
        throw SteghideError(_("could not get terminal attributes."));
    }

    curattr.c_lflag &= ~ECHO;

    if ((tcsetattr(STDIN_FILENO, TCSAFLUSH, &curattr)) != 0) {
        throw SteghideError(_("could not set terminal attributes."));
    }
}

void Terminal::SingleKeyOn() {
    struct termios curattr;
    if ((tcgetattr(STDIN_FILENO, &curattr)) != 0) {
        throw SteghideError(_("could not get terminal attributes."));
    }

    curattr.c_lflag &= ~ICANON;
    curattr.c_cc[VTIME] = 0;
    curattr.c_cc[VMIN] = 1;

    if ((tcsetattr(STDIN_FILENO, TCSAFLUSH, &curattr)) != 0) {
        throw SteghideError(_("could not set terminal attributes."));
    }
}

void Terminal::reset() {
    if ((tcsetattr(STDIN_FILENO, TCSANOW, &InitAttr)) != 0) {
        throw SteghideError(_("could not set terminal attributes."));
    }
}
#elif defined(_WIN32)
Terminal::Terminal() {
    InputHandle = GetStdHandle(STD_INPUT_HANDLE);
    IsConsole = GetConsoleMode(InputHandle, &InitMode) != 0;
}
void Terminal::EchoOff() {
    if (IsConsole && !SetConsoleMode(InputHandle, InitMode & ~ENABLE_ECHO_INPUT)) {
        throw SteghideError("could not disable terminal echo.");
    }
}
void Terminal::SingleKeyOn() {
    DWORD mode;
    if (IsConsole && (!GetConsoleMode(InputHandle, &mode) ||
                     !SetConsoleMode(InputHandle, mode & ~ENABLE_LINE_INPUT))) {
        throw SteghideError("could not set terminal input mode.");
    }
}
void Terminal::reset() {
    if (IsConsole && !SetConsoleMode(InputHandle, InitMode)) {
        throw SteghideError("could not restore terminal input mode.");
    }
}
#else
// TODO - do something that makes more sense - especially on Windows systems
Terminal::Terminal() {}
void Terminal::EchoOff() {}
void Terminal::SingleKeyOn() {}
void Terminal::reset() {}
#endif // def HAVE_TERMIOS_H
