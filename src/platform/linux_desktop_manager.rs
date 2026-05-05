     1|use super::{linux::*, ResultType};
     2|use crate::client::{
     3|    LOGIN_MSG_DESKTOP_NO_DESKTOP, LOGIN_MSG_DESKTOP_SESSION_ANOTHER_USER,
     4|    LOGIN_MSG_DESKTOP_SESSION_NOT_READY, LOGIN_MSG_DESKTOP_XORG_NOT_FOUND,
     5|    LOGIN_MSG_DESKTOP_XSESSION_FAILED,
     6|};
     7|use hbb_common::{
     8|    allow_err, bail, log,
     9|    rand::prelude::*,
    10|    tokio::time,
    11|    users::{get_user_by_name, os::unix::UserExt, User},
    12|};
    13|#[cfg(feature = "pam")]
    14|use pam;
    15|use std::{
    16|    collections::HashMap,
    17|    os::unix::process::CommandExt,
    18|    path::Path,
    19|    process::{Child, Command},
    20|    sync::{
    21|        atomic::{AtomicBool, Ordering},
    22|        mpsc::{sync_channel, SyncSender},
    23|        Arc, Mutex,
    24|    },
    25|    time::{Duration, Instant},
    26|};
    27|
    28|lazy_static::lazy_static! {
    29|    static ref DESKTOP_RUNNING: Arc<AtomicBool> = Arc::new(AtomicBool::new(false));
    30|    static ref DESKTOP_MANAGER: Arc<Mutex<Option<DesktopManager>>> = Arc::new(Mutex::new(None));
    31|}
    32|
    33|#[derive(Debug)]
    34|struct DesktopManager {
    35|    seat0_username: String,
    36|    seat0_display_server: String,
    37|    child_username: String,
    38|    child_exit: Arc<AtomicBool>,
    39|    is_child_running: Arc<AtomicBool>,
    40|}
    41|
    42|fn check_desktop_manager() {
    43|    let mut desktop_manager = DESKTOP_MANAGER.lock().unwrap();
    44|    if let Some(desktop_manager) = &mut (*desktop_manager) {
    45|        if desktop_manager.is_child_running.load(Ordering::SeqCst) {
    46|            return;
    47|        }
    48|        desktop_manager.child_exit.store(true, Ordering::SeqCst);
    49|    }
    50|}
    51|
    52|pub fn start_xdesktop() {
    53|    debug_assert!(crate::is_server());
    54|    std::thread::spawn(|| {
    55|        *DESKTOP_MANAGER.lock().unwrap() = Some(DesktopManager::new());
    56|
    57|        let interval = time::Duration::from_millis(super::SERVICE_INTERVAL);
    58|        DESKTOP_RUNNING.store(true, Ordering::SeqCst);
    59|        while DESKTOP_RUNNING.load(Ordering::SeqCst) {
    60|            check_desktop_manager();
    61|            std::thread::sleep(interval);
    62|        }
    63|        log::info!("xdesktop child thread exit");
    64|    });
    65|}
    66|
    67|pub fn stop_xdesktop() {
    68|    DESKTOP_RUNNING.store(false, Ordering::SeqCst);
    69|    *DESKTOP_MANAGER.lock().unwrap() = None;
    70|}
    71|
    72|fn detect_headless() -> Option<&'static str> {
    73|    match run_cmds(&format!("which {}", DesktopManager::get_xorg())) {
    74|        Ok(output) => {
    75|            if output.trim().is_empty() {
    76|                return Some(LOGIN_MSG_DESKTOP_XORG_NOT_FOUND);
    77|            }
    78|        }
    79|        _ => {
    80|            return Some(LOGIN_MSG_DESKTOP_XORG_NOT_FOUND);
    81|        }
    82|    }
    83|
    84|    match run_cmds("ls /usr/share/xsessions/") {
    85|        Ok(output) => {
    86|            if output.trim().is_empty() {
    87|                return Some(LOGIN_MSG_DESKTOP_NO_DESKTOP);
    88|            }
    89|        }
    90|        _ => {
    91|            return Some(LOGIN_MSG_DESKTOP_NO_DESKTOP);
    92|        }
    93|    }
    94|
    95|    None
    96|}
    97|
    98|pub fn try_start_desktop(_username: &str, _passsword: &str) -> String {
    99|    debug_assert!(crate::is_server());
   100|    if _username.is_empty() {
   101|        let username = get_username();
   102|        if username.is_empty() {
   103|            if let Some(msg) = detect_headless() {
   104|                msg
   105|            } else {
   106|                LOGIN_MSG_DESKTOP_SESSION_NOT_READY
   107|            }
   108|        } else {
   109|            ""
   110|        }
   111|        .to_owned()
   112|    } else {
   113|        let username = get_username();
   114|        if username == _username {
   115|            // No need to verify password here.
   116|            return "".to_owned();
   117|        }
   118|        if !username.is_empty() {
   119|            // Another user is logged in. No need to start a new xsession.
   120|            return "".to_owned();
   121|        }
   122|
   123|        if let Some(msg) = detect_headless() {
   124|            return msg.to_owned();
   125|        }
   126|
   127|        match try_start_x_session(_username, _passsword) {
   128|            Ok((username, x11_ready)) => {
   129|                if x11_ready {
   130|                    if _username != username {
   131|                        LOGIN_MSG_DESKTOP_SESSION_ANOTHER_USER.to_owned()
   132|                    } else {
   133|                        "".to_owned()
   134|                    }
   135|                } else {
   136|                    LOGIN_MSG_DESKTOP_SESSION_NOT_READY.to_owned()
   137|                }
   138|            }
   139|            Err(e) => {
   140|                log::error!("Failed to start xsession {}", e);
   141|                LOGIN_MSG_DESKTOP_XSESSION_FAILED.to_owned()
   142|            }
   143|        }
   144|    }
   145|}
   146|
   147|fn try_start_x_session(username: &str, password: &str) -> ResultType<(String, bool)> {
   148|    let mut desktop_manager = DESKTOP_MANAGER.lock().unwrap();
   149|    if let Some(desktop_manager) = &mut (*desktop_manager) {
   150|        if let Some(seat0_username) = desktop_manager.get_supported_display_seat0_username() {
   151|            return Ok((seat0_username, true));
   152|        }
   153|
   154|        let _ = desktop_manager.try_start_x_session(username, password)?;
   155|        log::debug!(
   156|            "try_start_x_session, username: {}, {:?}",
   157|            &username,
   158|            &desktop_manager
   159|        );
   160|        Ok((
   161|            desktop_manager.child_username.clone(),
   162|            desktop_manager.is_running(),
   163|        ))
   164|    } else {
   165|        bail!(crate::client::LOGIN_MSG_DESKTOP_NOT_INITED);
   166|    }
   167|}
   168|
   169|#[inline]
   170|pub fn is_headless() -> bool {
   171|    DESKTOP_MANAGER
   172|        .lock()
   173|        .unwrap()
   174|        .as_ref()
   175|        .map_or(false, |manager| {
   176|            manager.get_supported_display_seat0_username().is_none()
   177|        })
   178|}
   179|
   180|pub fn get_username() -> String {
   181|    match &*DESKTOP_MANAGER.lock().unwrap() {
   182|        Some(manager) => {
   183|            if let Some(seat0_username) = manager.get_supported_display_seat0_username() {
   184|                seat0_username
   185|            } else {
   186|                if manager.is_running() && !manager.child_username.is_empty() {
   187|                    manager.child_username.clone()
   188|                } else {
   189|                    "".to_owned()
   190|                }
   191|            }
   192|        }
   193|        None => "".to_owned(),
   194|    }
   195|}
   196|
   197|impl Drop for DesktopManager {
   198|    fn drop(&mut self) {
   199|        self.stop_children();
   200|    }
   201|}
   202|
   203|impl DesktopManager {
   204|    fn fatal_exit() {
   205|        std::process::exit(0);
   206|    }
   207|
   208|    pub fn new() -> Self {
   209|        let mut seat0_username = "".to_owned();
   210|        let mut seat0_display_server = "".to_owned();
   211|        let seat0_values = get_values_of_seat0(&[0, 2]);
   212|        if !seat0_values[0].is_empty() {
   213|            seat0_username = seat0_values[1].clone();
   214|            seat0_display_server = get_display_server_of_session(&seat0_values[0]);
   215|        }
   216|        Self {
   217|            seat0_username,
   218|            seat0_display_server,
   219|            child_username: "".to_owned(),
   220|            child_exit: Arc::new(AtomicBool::new(true)),
   221|            is_child_running: Arc::new(AtomicBool::new(false)),
   222|        }
   223|    }
   224|
   225|    fn get_supported_display_seat0_username(&self) -> Option<String> {
   226|        if is_gdm_user(&self.seat0_username) && self.seat0_display_server == DISPLAY_SERVER_WAYLAND
   227|        {
   228|            None
   229|        } else if self.seat0_username.is_empty() {
   230|            None
   231|        } else {
   232|            Some(self.seat0_username.clone())
   233|        }
   234|    }
   235|
   236|    #[inline]
   237|    fn get_xauth() -> String {
   238|        let xauth = get_env_var("XAUTHORITY");
   239|        if xauth.is_empty() {
   240|            "/tmp/.Xauthority".to_owned()
   241|        } else {
   242|            xauth
   243|        }
   244|    }
   245|
   246|    #[inline]
   247|    fn is_running(&self) -> bool {
   248|        self.is_child_running.load(Ordering::SeqCst)
   249|    }
   250|
   251|    fn try_start_x_session(&mut self, username: &str, password: &str) -> ResultType<()> {
   252|        match get_user_by_name(username) {
   253|            Some(userinfo) => {
#[cfg(feature = "pam")]
   254|                let mut client = pam::Client::with_password(&pam_get_service_name())?;
   255|                client
   256|                    .conversation_mut()
   257|                    .set_credentials(username, password);
   258|                match client.authenticate() {
   259|                    Ok(_) => {
   260|                        if self.is_running() {
   261|                            return Ok(());
   262|                        }
   263|
   264|                        match self.start_x_session(&userinfo, username, password) {
   265|                            Ok(_) => {
   266|                                log::info!("Succeeded to start x11");
   267|                                self.child_username = username.to_string();
   268|                                Ok(())
   269|                            }
   270|                            Err(e) => {
   271|                                bail!("failed to start x session, {}", e);
   272|                            }
   273|                        }
   274|                    }
   275|                    Err(e) => {
   276|                        bail!("failed to check user pass for {}, {}", username, e);
   277|                    }
   278|                }
   279|            }
   280|            None => {
   281|                bail!("failed to get userinfo of {}", username);
   282|            }
   283|        }
   284|    }
   285|
   286|    // The logic mainly from https://github.com/neutrinolabs/xrdp/blob/34fe9b60ebaea59e8814bbc3ca5383cabaa1b869/sesman/session.c#L334.
   287|    fn get_avail_display() -> ResultType<u32> {
   288|        let display_range = 0..51;
   289|        for i in display_range.clone() {
   290|            if Self::is_x_server_running(i) {
   291|                continue;
   292|            }
   293|            return Ok(i);
   294|        }
   295|        bail!("No available display found in range {:?}", display_range)
   296|    }
   297|
   298|    #[inline]
   299|    fn is_x_server_running(display: u32) -> bool {
   300|        Path::new(&format!("/tmp/.X11-unix/X{}", display)).exists()
   301|            || Path::new(&format!("/tmp/.X{}-lock", display)).exists()
   302|    }
   303|
   304|    fn start_x_session(
   305|        &mut self,
   306|        userinfo: &User,
   307|        username: &str,
   308|        password: &str,
   309|    ) -> ResultType<()> {
   310|        self.stop_children();
   311|
   312|        let display_num = Self::get_avail_display()?;
   313|        // "xServer_ip:display_num.screen_num"
   314|
   315|        let uid = userinfo.uid();
   316|        let gid = userinfo.primary_group_id();
   317|        let envs = HashMap::from([
   318|            ("SHELL", userinfo.shell().to_string_lossy().to_string()),
   319|            ("PATH", "/sbin:/bin:/usr/bin:/usr/local/bin".to_owned()),
   320|            ("USER", username.to_string()),
   321|            ("UID", userinfo.uid().to_string()),
   322|            ("HOME", userinfo.home_dir().to_string_lossy().to_string()),
   323|            (
   324|                "XDG_RUNTIME_DIR",
   325|                format!("/run/user/{}", userinfo.uid().to_string()),
   326|            ),
   327|            // ("DISPLAY", self.display.clone()),
   328|            // ("XAUTHORITY", self.xauth.clone()),
   329|            // (ENV_DESKTOP_PROTOCOL, XProtocol::X11.to_string()),
   330|        ]);
   331|        self.child_exit.store(false, Ordering::SeqCst);
   332|        let is_child_running = self.is_child_running.clone();
   333|
   334|        let (tx_res, rx_res) = sync_channel(1);
   335|        let password = password.to_string();
   336|        let username = username.to_string();
   337|        // start x11
   338|        std::thread::spawn(move || {
   339|            match Self::start_x_session_thread(
   340|                tx_res.clone(),
   341|                is_child_running,
   342|                uid,
   343|                gid,
   344|                display_num,
   345|                username,
   346|                password,
   347|                envs,
   348|            ) {
   349|                Ok(_) => {}
   350|                Err(e) => {
   351|                    log::error!("Failed to start x session thread");
   352|                    allow_err!(tx_res.send(format!("Failed to start x session thread, {}", e)));
   353|                }
   354|            }
   355|        });
   356|
   357|        // wait x11
   358|        match rx_res.recv_timeout(Duration::from_millis(10_000)) {
   359|            Ok(res) => {
   360|                if res == "" {
   361|                    Ok(())
   362|                } else {
   363|                    bail!(res)
   364|                }
   365|            }
   366|            Err(e) => {
   367|                bail!("Failed to recv x11 result {}", e)
   368|            }
   369|        }
   370|    }
   371|
   372|    #[inline]
   373|    fn display_from_num(num: u32) -> String {
   374|        format!(":{num}")
   375|    }
   376|
   377|    fn start_x_session_thread(
   378|        tx_res: SyncSender<String>,
   379|        is_child_running: Arc<AtomicBool>,
   380|        uid: u32,
   381|        gid: u32,
   382|        display_num: u32,
   383|        username: String,
   384|        password: String,
   385|        envs: HashMap<&str, String>,
   386|    ) -> ResultType<()> {
#[cfg(feature = "pam")]
   387|        let mut client = pam::Client::with_password(&pam_get_service_name())?;
   388|        client
   389|            .conversation_mut()
   390|            .set_credentials(&username, &password);
   391|        client.authenticate()?;
   392|
#[cfg(feature = "pam")]
   393|        client.set_item(pam::PamItemType::TTY, &Self::display_from_num(display_num))?;
   394|        client.open_session()?;
   395|
   396|        // fixme: FreeBSD kernel needs to login here.
   397|        // see: https://github.com/neutrinolabs/xrdp/blob/a64573b596b5fb07ca3a51590c5308d621f7214e/sesman/session.c#L556
   398|
   399|        let (child_xorg, child_wm) = Self::start_x11(uid, gid, username, display_num, &envs)?;
   400|        is_child_running.store(true, Ordering::SeqCst);
   401|
   402|        log::info!("Start xorg and wm done, notify and wait xtop x11");
   403|        allow_err!(tx_res.send("".to_owned()));
   404|
   405|        Self::wait_stop_x11(child_xorg, child_wm);
   406|        log::info!("Wait x11 stop done");
   407|        Ok(())
   408|    }
   409|
   410|    fn wait_xorg_exit(child_xorg: &mut Child) -> ResultType<String> {
   411|        if let Ok(_) = child_xorg.kill() {
   412|            for _ in 0..3 {
   413|                match child_xorg.try_wait() {
   414|                    Ok(Some(status)) => return Ok(format!("Xorg exit with {}", status)),
   415|                    Ok(None) => {}
   416|                    Err(e) => {
   417|                        // fatal error
   418|                        log::error!("Failed to wait xorg process, {}", e);
   419|                        bail!("Failed to wait xorg process, {}", e)
   420|                    }
   421|                }
   422|                std::thread::sleep(std::time::Duration::from_millis(1_000));
   423|            }
   424|            log::error!("Failed to wait xorg process, not exit");
   425|            bail!("Failed to wait xorg process, not exit")
   426|        } else {
   427|            Ok("Xorg is already exited".to_owned())
   428|        }
   429|    }
   430|
   431|    fn add_xauth_cookie(
   432|        file: &str,
   433|        display: &str,
   434|        uid: u32,
   435|        gid: u32,
   436|        envs: &HashMap<&str, String>,
   437|    ) -> ResultType<()> {
   438|        let randstr = (0..16)
   439|            .map(|_| format!("{:02x}", random::<u8>()))
   440|            .collect::<String>();
   441|        let output = Command::new("xauth")
   442|            .uid(uid)
   443|            .gid(gid)
   444|            .envs(envs)
   445|            .args(vec!["-q", "-f", file, "add", display, ".", &randstr])
   446|            .output()?;
   447|        // xauth run success, even the following error occurs.
   448|        // Ok(Output { status: ExitStatus(unix_wait_status(0)), stdout: "", stderr: "xauth:  file .Xauthority does not exist\n" })
   449|        let errmsg = String::from_utf8_lossy(&output.stderr).to_string();
   450|        if !errmsg.is_empty() {
   451|            if !errmsg.contains("does not exist") {
   452|                bail!("Failed to launch xauth, {}", errmsg)
   453|            }
   454|        }
   455|        Ok(())
   456|    }
   457|
   458|    fn wait_x_server_running(pid: u32, display_num: u32, max_wait_secs: u64) -> ResultType<()> {
   459|        let wait_begin = Instant::now();
   460|        loop {
   461|            if run_cmds(&format!("ls /proc/{}", pid))?.is_empty() {
   462|                bail!("X server exit");
   463|            }
   464|
   465|            if Self::is_x_server_running(display_num) {
   466|                return Ok(());
   467|            }
   468|            if wait_begin.elapsed().as_secs() > max_wait_secs {
   469|                bail!("Failed to wait xserver after {} seconds", max_wait_secs);
   470|            }
   471|            std::thread::sleep(Duration::from_millis(300));
   472|        }
   473|    }
   474|
   475|    fn start_x11(
   476|        uid: u32,
   477|        gid: u32,
   478|        username: String,
   479|        display_num: u32,
   480|        envs: &HashMap<&str, String>,
   481|    ) -> ResultType<(Child, Child)> {
   482|        log::debug!("envs of user {}: {:?}", &username, &envs);
   483|
   484|        let xauth = Self::get_xauth();
   485|        let display = Self::display_from_num(display_num);
   486|
   487|        Self::add_xauth_cookie(&xauth, &display, uid, gid, &envs)?;
   488|
   489|        // Start Xorg
   490|        let mut child_xorg = Self::start_x_server(&xauth, &display, uid, gid, &envs)?;
   491|
   492|        log::info!("xorg started, wait 10 secs to ensuer x server is running");
   493|
   494|        let max_wait_secs = 10;
   495|        // wait x server running
   496|        if let Err(e) = Self::wait_x_server_running(child_xorg.id(), display_num, max_wait_secs) {
   497|            match Self::wait_xorg_exit(&mut child_xorg) {
   498|                Ok(msg) => log::info!("{}", msg),
   499|                Err(e) => {
   500|                    log::error!("{}", e);
   501|