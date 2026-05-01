     1|use std::{
     2|    collections::HashMap,
     3|    future::Future,
     4|    net::{SocketAddr, ToSocketAddrs},
     5|    sync::{Arc, Mutex, RwLock},
     6|    task::Poll,
     7|};
     8|
     9|use serde_json::{json, Map, Value};
    10|
    11|#[cfg(not(target_os = "ios"))]
    12|use hbb_common::whoami;
    13|use hbb_common::{
    14|    allow_err,
    15|    anyhow::{anyhow, Context},
    16|    async_recursion::async_recursion,
    17|    bail, base64,
    18|    bytes::Bytes,
    19|    config::{
    20|        self, keys, use_ws, Config, LocalConfig, CONNECT_TIMEOUT, READ_TIMEOUT, RENDEZVOUS_PORT,
    21|    },
    22|    futures::future::join_all,
    23|    futures_util::future::poll_fn,
    24|    get_version_number, log,
    25|    message_proto::*,
    26|    protobuf::{Enum, Message as _},
    27|    rendezvous_proto::*,
    28|    socket_client,
    29|    sodiumoxide::crypto::{box_, secretbox, sign},
    30|    timeout,
    31|    tls::{get_cached_tls_accept_invalid_cert, get_cached_tls_type, upsert_tls_cache, TlsType},
    32|    tokio::{
    33|        self,
    34|        net::UdpSocket,
    35|        time::{Duration, Instant, Interval},
    36|    },
    37|    ResultType, Stream,
    38|};
    39|
    40|use crate::{
    41|    hbbs_http::{create_http_client_async, get_url_for_tls},
    42|    ui_interface::{get_option, set_option},
    43|};
    44|
    45|#[derive(Debug, Eq, PartialEq)]
    46|pub enum GrabState {
    47|    Ready,
    48|    Run,
    49|    Wait,
    50|    Exit,
    51|}
    52|
    53|pub type NotifyMessageBox = fn(String, String, String, String) -> dyn Future<Output = ()>;
    54|
    55|// the executable name of the portable version
    56|pub const PORTABLE_APPNAME_RUNTIME_ENV_KEY: &str = "RUSTDESK_APPNAME";
    57|
    58|pub const PLATFORM_WINDOWS: &str = "Windows";
    59|pub const PLATFORM_LINUX: &str = "Linux";
    60|pub const PLATFORM_MACOS: &str = "Mac OS";
    61|pub const PLATFORM_ANDROID: &str = "Android";
    62|
    63|pub const TIMER_OUT: Duration = Duration::from_secs(1);
    64|pub const DEFAULT_KEEP_ALIVE: i32 = 60_000;
    65|
    66|const MIN_VER_MULTI_UI_SESSION: &str = "1.2.4";
    67|
    68|pub mod input {
    69|    pub const MOUSE_TYPE_MOVE: i32 = 0;
    70|    pub const MOUSE_TYPE_DOWN: i32 = 1;
    71|    pub const MOUSE_TYPE_UP: i32 = 2;
    72|    pub const MOUSE_TYPE_WHEEL: i32 = 3;
    73|    pub const MOUSE_TYPE_TRACKPAD: i32 = 4;
    74|    /// Relative mouse movement type for gaming/3D applications.
    75|    /// This type sends delta (dx, dy) values instead of absolute coordinates.
    76|    /// NOTE: This is only supported by the Flutter client. The Sciter client (deprecated)
    77|    /// does not support relative mouse mode due to:
    78|    /// 1. Fixed send_mouse() function signature that doesn't allow type differentiation
    79|    /// 2. Lack of pointer lock API in Sciter/TIS
    80|    /// 3. No OS cursor control (hide/show/clip) FFI bindings in Sciter UI
    81|    pub const MOUSE_TYPE_MOVE_RELATIVE: i32 = 5;
    82|
    83|    /// Mask to extract the mouse event type from the mask field.
    84|    /// The lower 3 bits contain the event type (MOUSE_TYPE_*), giving a valid range of 0-7.
    85|    /// Currently defined types use values 0-5; values 6 and 7 are reserved for future use.
    86|    pub const MOUSE_TYPE_MASK: i32 = 0x7;
    87|
    88|    pub const MOUSE_BUTTON_LEFT: i32 = 0x01;
    89|    pub const MOUSE_BUTTON_RIGHT: i32 = 0x02;
    90|    pub const MOUSE_BUTTON_WHEEL: i32 = 0x04;
    91|    pub const MOUSE_BUTTON_BACK: i32 = 0x08;
    92|    pub const MOUSE_BUTTON_FORWARD: i32 = 0x10;
    93|}
    94|
    95|lazy_static::lazy_static! {
    96|    pub static ref SOFTWARE_UPDATE_URL: Arc<Mutex<String>> = Default::default();
    97|    pub static ref DEVICE_ID: Arc<Mutex<String>> = Default::default();
    98|    pub static ref DEVICE_NAME: Arc<Mutex<String>> = Default::default();
    99|    static ref PUBLIC_IPV6_ADDR: Arc<Mutex<(Option<SocketAddr>, Option<Instant>)>> = Default::default();
   100|}
   101|
   102|lazy_static::lazy_static! {
   103|    // Is server process, with "--server" args
   104|    static ref IS_SERVER: bool = std::env::args().nth(1) == Some("--server".to_owned());
   105|    // Is server logic running. The server code can invoked to run by the main process if --server is not running.
   106|    static ref SERVER_RUNNING: Arc<RwLock<bool>> = Default::default();
   107|    static ref IS_MAIN: bool = std::env::args().nth(1).map_or(true, |arg| !arg.starts_with("--"));
   108|    static ref IS_CM: bool = std::env::args().nth(1) == Some("--cm".to_owned()) || std::env::args().nth(1) == Some("--cm-no-ui".to_owned());
   109|}
   110|
   111|pub struct SimpleCallOnReturn {
   112|    pub b: bool,
   113|    pub f: Box<dyn Fn() + Send + 'static>,
   114|}
   115|
   116|impl Drop for SimpleCallOnReturn {
   117|    fn drop(&mut self) {
   118|        if self.b {
   119|            (self.f)();
   120|        }
   121|    }
   122|}
   123|
   124|pub fn global_init() -> bool {
   125|    #[cfg(target_os = "linux")]
   126|    {
   127|        if !crate::platform::linux::is_x11() {
   128|            crate::server::wayland::init();
   129|        }
   130|    }
   131|    true
   132|}
   133|
   134|pub fn global_clean() {}
   135|
   136|#[inline]
   137|pub fn set_server_running(b: bool) {
   138|    *SERVER_RUNNING.write().unwrap() = b;
   139|}
   140|
   141|#[inline]
   142|pub fn is_support_multi_ui_session(ver: &str) -> bool {
   143|    is_support_multi_ui_session_num(hbb_common::get_version_number(ver))
   144|}
   145|
   146|#[inline]
   147|pub fn is_support_multi_ui_session_num(ver: i64) -> bool {
   148|    ver >= hbb_common::get_version_number(MIN_VER_MULTI_UI_SESSION)
   149|}
   150|
   151|#[inline]
   152|#[cfg(feature = "unix-file-copy-paste")]
   153|pub fn is_support_file_copy_paste(ver: &str) -> bool {
   154|    is_support_file_copy_paste_num(hbb_common::get_version_number(ver))
   155|}
   156|
   157|#[inline]
   158|#[cfg(feature = "unix-file-copy-paste")]
   159|pub fn is_support_file_copy_paste_num(ver: i64) -> bool {
   160|    ver >= hbb_common::get_version_number("1.3.8")
   161|}
   162|
   163|pub fn is_support_remote_print(ver: &str) -> bool {
   164|    hbb_common::get_version_number(ver) >= hbb_common::get_version_number("1.3.9")
   165|}
   166|
   167|pub fn is_support_file_paste_if_macos(ver: &str) -> bool {
   168|    hbb_common::get_version_number(ver) >= hbb_common::get_version_number("1.3.9")
   169|}
   170|
   171|#[inline]
   172|pub fn is_support_screenshot(ver: &str) -> bool {
   173|    is_support_multi_ui_session_num(hbb_common::get_version_number(ver))
   174|}
   175|
   176|#[inline]
   177|pub fn is_support_screenshot_num(ver: i64) -> bool {
   178|    ver >= hbb_common::get_version_number("1.4.0")
   179|}
   180|
   181|#[inline]
   182|pub fn is_support_file_transfer_resume(ver: &str) -> bool {
   183|    is_support_file_transfer_resume_num(hbb_common::get_version_number(ver))
   184|}
   185|
   186|#[inline]
   187|pub fn is_support_file_transfer_resume_num(ver: i64) -> bool {
   188|    ver >= hbb_common::get_version_number("1.4.2")
   189|}
   190|
   191|/// Minimum server version required for relative mouse mode support.
   192|/// This constant must mirror Flutter's `kMinVersionForRelativeMouseMode` in `consts.dart`.
   193|const MIN_VERSION_RELATIVE_MOUSE_MODE: &str = "1.4.5";
   194|
   195|#[inline]
   196|pub fn is_support_relative_mouse_mode(ver: &str) -> bool {
   197|    is_support_relative_mouse_mode_num(hbb_common::get_version_number(ver))
   198|}
   199|
   200|#[inline]
   201|pub fn is_support_relative_mouse_mode_num(ver: i64) -> bool {
   202|    ver >= hbb_common::get_version_number(MIN_VERSION_RELATIVE_MOUSE_MODE)
   203|}
   204|
   205|// is server process, with "--server" args
   206|#[inline]
   207|pub fn is_server() -> bool {
   208|    *IS_SERVER
   209|}
   210|
   211|#[inline]
   212|pub fn need_fs_cm_send_files() -> bool {
   213|    #[cfg(windows)]
   214|    {
   215|        is_server()
   216|    }
   217|    #[cfg(not(windows))]
   218|    {
   219|        false
   220|    }
   221|}
   222|
   223|#[inline]
   224|pub fn is_main() -> bool {
   225|    *IS_MAIN
   226|}
   227|
   228|#[inline]
   229|pub fn is_cm() -> bool {
   230|    *IS_CM
   231|}
   232|
   233|// Is server logic running.
   234|#[inline]
   235|pub fn is_server_running() -> bool {
   236|    *SERVER_RUNNING.read().unwrap()
   237|}
   238|
   239|#[inline]
   240|pub fn valid_for_numlock(evt: &KeyEvent) -> bool {
   241|    if let Some(key_event::Union::ControlKey(ck)) = evt.union {
   242|        let v = ck.value();
   243|        (v >= ControlKey::Numpad0.value() && v <= ControlKey::Numpad9.value())
   244|            || v == ControlKey::Decimal.value()
   245|    } else {
   246|        false
   247|    }
   248|}
   249|
   250|/// Set sound input device.
   251|pub fn set_sound_input(device: String) {
   252|    let prior_device = get_option("audio-input".to_owned());
   253|    if prior_device != device {
   254|        log::info!("switch to audio input device {}", device);
   255|        std::thread::spawn(move || {
   256|            set_option("audio-input".to_owned(), device);
   257|        });
   258|    } else {
   259|        log::info!("audio input is already set to {}", device);
   260|    }
   261|}
   262|
   263|/// Get system's default sound input device name.
   264|#[inline]
   265|#[cfg(not(any(target_os = "android", target_os = "ios")))]
   266|pub fn get_default_sound_input() -> Option<String> {
   267|    #[cfg(not(target_os = "linux"))]
   268|    {
   269|        use cpal::traits::{DeviceTrait, HostTrait};
   270|        let host = cpal::default_host();
   271|        let dev = host.default_input_device();
   272|        return if let Some(dev) = dev {
   273|            match dev.name() {
   274|                Ok(name) => Some(name),
   275|                Err(_) => None,
   276|            }
   277|        } else {
   278|            None
   279|        };
   280|    }
   281|    #[cfg(target_os = "linux")]
   282|    {
   283|        let input = crate::platform::linux::get_default_pa_source();
   284|        return if let Some(input) = input {
   285|            Some(input.1)
   286|        } else {
   287|            None
   288|        };
   289|    }
   290|}
   291|
   292|#[inline]
   293|#[cfg(any(target_os = "android", target_os = "ios"))]
   294|pub fn get_default_sound_input() -> Option<String> {
   295|    None
   296|}
   297|
   298|#[cfg(feature = "use_rubato")]
   299|pub fn resample_channels(
   300|    data: &[f32],
   301|    sample_rate0: u32,
   302|    sample_rate: u32,
   303|    channels: u16,
   304|) -> Vec<f32> {
   305|    use rubato::{
   306|        InterpolationParameters, InterpolationType, Resampler, SincFixedIn, WindowFunction,
   307|    };
   308|    let params = InterpolationParameters {
   309|        sinc_len: 256,
   310|        f_cutoff: 0.95,
   311|        interpolation: InterpolationType::Nearest,
   312|        oversampling_factor: 160,
   313|        window: WindowFunction::BlackmanHarris2,
   314|    };
   315|    let mut resampler = SincFixedIn::<f64>::new(
   316|        sample_rate as f64 / sample_rate0 as f64,
   317|        params,
   318|        data.len() / (channels as usize),
   319|        channels as _,
   320|    );
   321|    let mut waves_in = Vec::new();
   322|    if channels == 2 {
   323|        waves_in.push(
   324|            data.iter()
   325|                .step_by(2)
   326|                .map(|x| *x as f64)
   327|                .collect::<Vec<_>>(),
   328|        );
   329|        waves_in.push(
   330|            data.iter()
   331|                .skip(1)
   332|                .step_by(2)
   333|                .map(|x| *x as f64)
   334|                .collect::<Vec<_>>(),
   335|        );
   336|    } else {
   337|        waves_in.push(data.iter().map(|x| *x as f64).collect::<Vec<_>>());
   338|    }
   339|    if let Ok(x) = resampler.process(&waves_in) {
   340|        if x.is_empty() {
   341|            Vec::new()
   342|        } else if x.len() == 2 {
   343|            x[0].chunks(1)
   344|                .zip(x[1].chunks(1))
   345|                .flat_map(|(a, b)| a.into_iter().chain(b))
   346|                .map(|x| *x as f32)
   347|                .collect()
   348|        } else {
   349|            x[0].iter().map(|x| *x as f32).collect()
   350|        }
   351|    } else {
   352|        Vec::new()
   353|    }
   354|}
   355|
   356|#[cfg(feature = "use_dasp")]
   357|pub fn audio_resample(
   358|    data: &[f32],
   359|    sample_rate0: u32,
   360|    sample_rate: u32,
   361|    channels: u16,
   362|) -> Vec<f32> {
   363|    use dasp::{interpolate::linear::Linear, signal, Signal};
   364|    let n = data.len() / (channels as usize);
   365|    let n = n * sample_rate as usize / sample_rate0 as usize;
   366|    if channels == 2 {
   367|        let mut source = signal::from_interleaved_samples_iter::<_, [_; 2]>(data.iter().cloned());
   368|        let a = source.next();
   369|        let b = source.next();
   370|        let interp = Linear::new(a, b);
   371|        let mut data = Vec::with_capacity(n << 1);
   372|        for x in source
   373|            .from_hz_to_hz(interp, sample_rate0 as _, sample_rate as _)
   374|            .take(n)
   375|        {
   376|            data.push(x[0]);
   377|            data.push(x[1]);
   378|        }
   379|        data
   380|    } else {
   381|        let mut source = signal::from_iter(data.iter().cloned());
   382|        let a = source.next();
   383|        let b = source.next();
   384|        let interp = Linear::new(a, b);
   385|        source
   386|            .from_hz_to_hz(interp, sample_rate0 as _, sample_rate as _)
   387|            .take(n)
   388|            .collect()
   389|    }
   390|}
   391|
   392|#[cfg(feature = "use_samplerate")]
   393|pub fn audio_resample(
   394|    data: &[f32],
   395|    sample_rate0: u32,
   396|    sample_rate: u32,
   397|    channels: u16,
   398|) -> Vec<f32> {
   399|    use samplerate::{convert, ConverterType};
   400|    convert(
   401|        sample_rate0 as _,
   402|        sample_rate as _,
   403|        channels as _,
   404|        ConverterType::SincBestQuality,
   405|        data,
   406|    )
   407|    .unwrap_or_default()
   408|}
   409|
   410|pub fn audio_rechannel(
   411|    input: Vec<f32>,
   412|    in_hz: u32,
   413|    out_hz: u32,
   414|    in_chan: u16,
   415|    output_chan: u16,
   416|) -> Vec<f32> {
   417|    if in_chan == output_chan {
   418|        return input;
   419|    }
   420|    let mut input = input;
   421|    input.truncate(input.len() / in_chan as usize * in_chan as usize);
   422|    match (in_chan, output_chan) {
   423|        (1, 2) => audio_rechannel_1_2(&input, in_hz, out_hz),
   424|        (1, 3) => audio_rechannel_1_3(&input, in_hz, out_hz),
   425|        (1, 4) => audio_rechannel_1_4(&input, in_hz, out_hz),
   426|        (1, 5) => audio_rechannel_1_5(&input, in_hz, out_hz),
   427|        (1, 6) => audio_rechannel_1_6(&input, in_hz, out_hz),
   428|        (1, 7) => audio_rechannel_1_7(&input, in_hz, out_hz),
   429|        (1, 8) => audio_rechannel_1_8(&input, in_hz, out_hz),
   430|        (2, 1) => audio_rechannel_2_1(&input, in_hz, out_hz),
   431|        (2, 3) => audio_rechannel_2_3(&input, in_hz, out_hz),
   432|        (2, 4) => audio_rechannel_2_4(&input, in_hz, out_hz),
   433|        (2, 5) => audio_rechannel_2_5(&input, in_hz, out_hz),
   434|        (2, 6) => audio_rechannel_2_6(&input, in_hz, out_hz),
   435|        (2, 7) => audio_rechannel_2_7(&input, in_hz, out_hz),
   436|        (2, 8) => audio_rechannel_2_8(&input, in_hz, out_hz),
   437|        (3, 1) => audio_rechannel_3_1(&input, in_hz, out_hz),
   438|        (3, 2) => audio_rechannel_3_2(&input, in_hz, out_hz),
   439|        (3, 4) => audio_rechannel_3_4(&input, in_hz, out_hz),
   440|        (3, 5) => audio_rechannel_3_5(&input, in_hz, out_hz),
   441|        (3, 6) => audio_rechannel_3_6(&input, in_hz, out_hz),
   442|        (3, 7) => audio_rechannel_3_7(&input, in_hz, out_hz),
   443|        (3, 8) => audio_rechannel_3_8(&input, in_hz, out_hz),
   444|        (4, 1) => audio_rechannel_4_1(&input, in_hz, out_hz),
   445|        (4, 2) => audio_rechannel_4_2(&input, in_hz, out_hz),
   446|        (4, 3) => audio_rechannel_4_3(&input, in_hz, out_hz),
   447|        (4, 5) => audio_rechannel_4_5(&input, in_hz, out_hz),
   448|        (4, 6) => audio_rechannel_4_6(&input, in_hz, out_hz),
   449|        (4, 7) => audio_rechannel_4_7(&input, in_hz, out_hz),
   450|        (4, 8) => audio_rechannel_4_8(&input, in_hz, out_hz),
   451|        (5, 1) => audio_rechannel_5_1(&input, in_hz, out_hz),
   452|        (5, 2) => audio_rechannel_5_2(&input, in_hz, out_hz),
   453|        (5, 3) => audio_rechannel_5_3(&input, in_hz, out_hz),
   454|        (5, 4) => audio_rechannel_5_4(&input, in_hz, out_hz),
   455|        (5, 6) => audio_rechannel_5_6(&input, in_hz, out_hz),
   456|        (5, 7) => audio_rechannel_5_7(&input, in_hz, out_hz),
   457|        (5, 8) => audio_rechannel_5_8(&input, in_hz, out_hz),
   458|        (6, 1) => audio_rechannel_6_1(&input, in_hz, out_hz),
   459|        (6, 2) => audio_rechannel_6_2(&input, in_hz, out_hz),
   460|        (6, 3) => audio_rechannel_6_3(&input, in_hz, out_hz),
   461|        (6, 4) => audio_rechannel_6_4(&input, in_hz, out_hz),
   462|        (6, 5) => audio_rechannel_6_5(&input, in_hz, out_hz),
   463|        (6, 7) => audio_rechannel_6_7(&input, in_hz, out_hz),
   464|        (6, 8) => audio_rechannel_6_8(&input, in_hz, out_hz),
   465|        (7, 1) => audio_rechannel_7_1(&input, in_hz, out_hz),
   466|        (7, 2) => audio_rechannel_7_2(&input, in_hz, out_hz),
   467|        (7, 3) => audio_rechannel_7_3(&input, in_hz, out_hz),
   468|        (7, 4) => audio_rechannel_7_4(&input, in_hz, out_hz),
   469|        (7, 5) => audio_rechannel_7_5(&input, in_hz, out_hz),
   470|        (7, 6) => audio_rechannel_7_6(&input, in_hz, out_hz),
   471|        (7, 8) => audio_rechannel_7_8(&input, in_hz, out_hz),
   472|        (8, 1) => audio_rechannel_8_1(&input, in_hz, out_hz),
   473|        (8, 2) => audio_rechannel_8_2(&input, in_hz, out_hz),
   474|        (8, 3) => audio_rechannel_8_3(&input, in_hz, out_hz),
   475|        (8, 4) => audio_rechannel_8_4(&input, in_hz, out_hz),
   476|        (8, 5) => audio_rechannel_8_5(&input, in_hz, out_hz),
   477|        (8, 6) => audio_rechannel_8_6(&input, in_hz, out_hz),
   478|        (8, 7) => audio_rechannel_8_7(&input, in_hz, out_hz),
   479|        _ => input,
   480|    }
   481|}
   482|
   483|macro_rules! audio_rechannel {
   484|    ($name:ident, $in_channels:expr, $out_channels:expr) => {
   485|        fn $name(input: &[f32], in_hz: u32, out_hz: u32) -> Vec<f32> {
   486|            use fon::{chan::Ch32, Audio, Frame};
   487|            let mut in_audio =
   488|                Audio::<Ch32, $in_channels>::with_silence(in_hz, input.len() / $in_channels);
   489|            for (x, y) in input.chunks_exact($in_channels).zip(in_audio.iter_mut()) {
   490|                let mut f = Frame::<Ch32, $in_channels>::default();
   491|                let mut i = 0;
   492|                for c in f.channels_mut() {
   493|                    *c = x[i].into();
   494|                    i += 1;
   495|                }
   496|                *y = f;
   497|            }
   498|            Audio::<Ch32, $out_channels>::with_audio(out_hz, &in_audio)
   499|                .as_f32_slice()
   500|                .to_owned()
   501|