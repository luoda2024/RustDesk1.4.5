//! Stub implementation of libxdo-sys for systems without libxdo
//! This allows building and running on systems without libxdo installed (e.g., Wayland-only)

use libc::{c_int, c_uint, c_void, c_char};

pub const CURRENTWINDOW: c_uint = 0;

pub type xdo_t = c_void;

#[no_mangle]
pub unsafe extern "C" fn xdo_new(_display: *const c_char) -> *mut xdo_t {
    std::ptr::null_mut()
}

#[no_mangle]
pub unsafe extern "C" fn xdo_free(_xdo: *mut xdo_t) {}

#[no_mangle]
pub unsafe extern "C" fn xdo_move_mouse(
    _xdo: *const xdo_t,
    _x: c_int,
    _y: c_int,
    _screen: c_int,
) -> c_int {
    0
}

#[no_mangle]
pub unsafe extern "C" fn xdo_move_mouse_relative(
    _xdo: *const xdo_t,
    _x: c_int,
    _y: c_int,
) -> c_int {
    0
}

#[no_mangle]
pub unsafe extern "C" fn xdo_mouse_down(
    _xdo: *const xdo_t,
    _window: c_uint,
    _button: c_int,
) -> c_int {
    0
}

#[no_mangle]
pub unsafe extern "C" fn xdo_mouse_up(
    _xdo: *const xdo_t,
    _window: c_uint,
    _button: c_int,
) -> c_int {
    0
}

#[no_mangle]
pub unsafe extern "C" fn xdo_click_window(
    _xdo: *const xdo_t,
    _window: c_uint,
    _button: c_int,
) -> c_int {
    0
}

#[no_mangle]
pub unsafe extern "C" fn xdo_get_input_state(_xdo: *const xdo_t) -> c_uint {
    0
}

#[no_mangle]
pub unsafe extern "C" fn xdo_enter_text_window(
    _xdo: *const xdo_t,
    _window: c_uint,
    _text: *const c_char,
    _delay: c_uint,
) -> c_int {
    0
}

#[no_mangle]
pub unsafe extern "C" fn xdo_send_keysequence_window_down(
    _xdo: *const xdo_t,
    _window: c_uint,
    _keysequence: *const c_char,
    _delay: c_uint,
) -> c_int {
    0
}

#[no_mangle]
pub unsafe extern "C" fn xdo_send_keysequence_window_up(
    _xdo: *const xdo_t,
    _window: c_uint,
    _keysequence: *const c_char,
    _delay: c_uint,
) -> c_int {
    0
}

#[no_mangle]
pub unsafe extern "C" fn xdo_send_keysequence_window(
    _xdo: *const xdo_t,
    _window: c_uint,
    _keysequence: *const c_char,
    _delay: c_uint,
) -> c_int {
    0
}

#[no_mangle]
pub unsafe extern "C" fn xdo_get_mouse_location(
    _xdo: *const xdo_t,
    _x: *mut c_int,
    _y: *mut c_int,
    _screen_num: *mut c_int,
) -> c_int {
    0
}

#[no_mangle]
pub unsafe extern "C" fn xdo_get_active_window(_xdo: *const xdo_t) -> c_uint {
    0
}

#[no_mangle]
pub unsafe extern "C" fn xdo_get_window_focus(_xdo: *const xdo_t) -> c_uint {
    0
}

#[no_mangle]
pub unsafe extern "C" fn xdo_get_window_pid(_xdo: *const xdo_t, _window: c_uint) -> c_uint {
    0
}