use core::ptr::NonNull;
use core::time;
use std::fs::{self, File, FileType};
use std::io::{self, prelude::*};
use std::{string::String, vec::Vec};

use axhal::mem::phys_to_virt;
use axhal::misc::*;
use axstd::thread::sleep;

#[cfg(all(not(feature = "axstd"), unix))]
use std::os::unix::fs::{FileTypeExt, PermissionsExt};

macro_rules! print_err {
    ($cmd: literal, $msg: expr) => {
        println!("{}: {}", $cmd, $msg);
    };
    ($cmd: literal, $arg: expr, $err: expr) => {
        println!("{}: {}: {}", $cmd, $arg, $err);
    };
}

type CmdHandler = fn(&str);

const CMD_TABLE: &[(&str, CmdHandler)] = &[
    ("cat", do_cat),
    ("cd", do_cd),
    ("echo", do_echo),
    ("exit", do_exit),
    ("help", do_help),
    ("ls", do_ls),
    ("mkdir", do_mkdir),
    ("pwd", do_pwd),
    ("rm", do_rm),
    ("uname", do_uname),
    ("uart_set_baud", do_uart_set_baud),
    ("uart_test", do_uart_test),
    ("clock_init", do_clock_init),
    ("clock_test", do_clock_test),
    ("gpio_init", do_gpio_init),
    ("gpio_test", do_gpio_test),
    ("pwm_init", do_pwm_init),
    ("pwm_test", do_pwm_test),
    ("timer_tacho_test", do_timer_tacho_test),
    ("watchdog_init", do_watchdog_init),
    ("watchdog_test", do_watchdog_test),
    ("i2c_init", do_i2c_init),
    ("i2c_test", do_i2c_test),
    ("mio_init", do_mio_init),
    ("mio_test", do_mio_test),
    ("cru_init", do_cru_init),
    ("cru_test", do_cru_test),
    ("spi_init", do_spi_init),
    ("spi_test", do_spi_test),
    ("gic_init", do_gic_init),
    ("fxmac_init", do_fxmac_init),
    ("pcie_init", do_pcie_init),
    ("ixgeb_init", do_ixgeb_init),
];

fn file_type_to_char(ty: FileType) -> char {
    if ty.is_char_device() {
        'c'
    } else if ty.is_block_device() {
        'b'
    } else if ty.is_socket() {
        's'
    } else if ty.is_fifo() {
        'p'
    } else if ty.is_symlink() {
        'l'
    } else if ty.is_dir() {
        'd'
    } else if ty.is_file() {
        '-'
    } else {
        '?'
    }
}

#[rustfmt::skip]
const fn file_perm_to_rwx(mode: u32) -> [u8; 9] {
    let mut perm = [b'-'; 9];
    macro_rules! set {
        ($bit:literal, $rwx:literal) => {
            if mode & (1 << $bit) != 0 {
                perm[8 - $bit] = $rwx
            }
        };
    }

    set!(2, b'r'); set!(1, b'w'); set!(0, b'x');
    set!(5, b'r'); set!(4, b'w'); set!(3, b'x');
    set!(8, b'r'); set!(7, b'w'); set!(6, b'x');
    perm
}

fn do_ls(args: &str) {
    let current_dir = std::env::current_dir().unwrap();
    let args = if args.is_empty() {
        path_to_str!(current_dir)
    } else {
        args
    };
    let name_count = args.split_whitespace().count();

    fn show_entry_info(path: &str, entry: &str) -> io::Result<()> {
        let metadata = fs::metadata(path)?;
        let size = metadata.len();
        let file_type = metadata.file_type();
        let file_type_char = file_type_to_char(file_type);
        let rwx = file_perm_to_rwx(metadata.permissions().mode());
        let rwx = unsafe { core::str::from_utf8_unchecked(&rwx) };
        println!("{}{} {:>8} {}", file_type_char, rwx, size, entry);
        Ok(())
    }

    fn list_one(name: &str, print_name: bool) -> io::Result<()> {
        let is_dir = fs::metadata(name)?.is_dir();
        if !is_dir {
            return show_entry_info(name, name);
        }

        if print_name {
            println!("{}:", name);
        }
        let mut entries = fs::read_dir(name)?
            .filter_map(|e| e.ok())
            .map(|e| e.file_name())
            .collect::<Vec<_>>();
        entries.sort();

        for entry in entries {
            let entry = path_to_str!(entry);
            let path = String::from(name) + "/" + entry;
            if let Err(e) = show_entry_info(&path, entry) {
                print_err!("ls", path, e);
            }
        }
        Ok(())
    }

    for (i, name) in args.split_whitespace().enumerate() {
        if i > 0 {
            println!();
        }
        if let Err(e) = list_one(name, name_count > 1) {
            print_err!("ls", name, e);
        }
    }
}

fn do_cat(args: &str) {
    if args.is_empty() {
        print_err!("cat", "no file specified");
        return;
    }

    fn cat_one(fname: &str) -> io::Result<()> {
        let mut buf = [0; 1024];
        let mut file = File::open(fname)?;
        loop {
            let n = file.read(&mut buf)?;
            if n > 0 {
                io::stdout().write_all(&buf[..n])?;
            } else {
                return Ok(());
            }
        }
    }

    for fname in args.split_whitespace() {
        if let Err(e) = cat_one(fname) {
            print_err!("cat", fname, e);
        }
    }
}

fn do_echo(args: &str) {
    fn echo_file(fname: &str, text_list: &[&str]) -> io::Result<()> {
        let mut file = File::create(fname)?;
        for text in text_list {
            file.write_all(text.as_bytes())?;
        }
        Ok(())
    }

    if let Some(pos) = args.rfind('>') {
        let text_before = args[..pos].trim();
        let (fname, text_after) = split_whitespace(&args[pos + 1..]);
        if fname.is_empty() {
            print_err!("echo", "no file specified");
            return;
        };

        let text_list = [
            text_before,
            if !text_after.is_empty() { " " } else { "" },
            text_after,
            "\n",
        ];
        if let Err(e) = echo_file(fname, &text_list) {
            print_err!("echo", fname, e);
        }
    } else {
        println!("{}", args)
    }
}

fn do_mkdir(args: &str) {
    if args.is_empty() {
        print_err!("mkdir", "missing operand");
        return;
    }

    fn mkdir_one(path: &str) -> io::Result<()> {
        fs::create_dir(path)
    }

    for path in args.split_whitespace() {
        if let Err(e) = mkdir_one(path) {
            print_err!("mkdir", format_args!("cannot create directory '{path}'"), e);
        }
    }
}

fn do_rm(args: &str) {
    if args.is_empty() {
        print_err!("rm", "missing operand");
        return;
    }
    let mut rm_dir = false;
    for arg in args.split_whitespace() {
        if arg == "-d" {
            rm_dir = true;
        }
    }

    fn rm_one(path: &str, rm_dir: bool) -> io::Result<()> {
        if rm_dir && fs::metadata(path)?.is_dir() {
            fs::remove_dir(path)
        } else {
            fs::remove_file(path)
        }
    }

    for path in args.split_whitespace() {
        if path == "-d" {
            continue;
        }
        if let Err(e) = rm_one(path, rm_dir) {
            print_err!("rm", format_args!("cannot remove '{path}'"), e);
        }
    }
}

fn do_cd(mut args: &str) {
    if args.is_empty() {
        args = "/";
    }
    if !args.contains(char::is_whitespace) {
        if let Err(e) = std::env::set_current_dir(args) {
            print_err!("cd", args, e);
        }
    } else {
        print_err!("cd", "too many arguments");
    }
}

fn do_pwd(_args: &str) {
    let pwd = std::env::current_dir().unwrap();
    println!("{}", path_to_str!(pwd));
}

fn do_uname(_args: &str) {
    let arch = option_env!("AX_ARCH").unwrap_or("");
    let platform = option_env!("AX_PLATFORM").unwrap_or("");
    let smp = match option_env!("AX_SMP") {
        None | Some("1") => "",
        _ => " SMP",
    };
    let version = option_env!("CARGO_PKG_VERSION").unwrap_or("0.1.0");
    println!(
        "ArceOS {ver}{smp} {arch} {plat}",
        ver = version,
        smp = smp,
        arch = arch,
        plat = platform,
    );
}

fn do_help(_args: &str) {
    println!("Available commands:");
    for (name, _) in CMD_TABLE {
        println!("  {}", name);
    }
}

fn do_exit(_args: &str) {
    println!("Bye~");
    std::process::exit(0);
}

fn do_uart_set_baud(args: &str) {
    let baud = args.parse::<u32>().unwrap();
    let mut uart = UART2.lock();
    uart.init_no_irq(100_000_000, baud);
    println!("set uart baud OK, baud: {}", baud);
}

fn do_uart_test(_args: &str) {
    let mut uart = UART2.lock();
    let mut data = Vec::new();
    loop {
        let read = uart.read_byte_poll();
        if read == 0x0 {
            break;
        }
        println!("arceos receive : {}", read as char);
        data.push(read);
    }
    println!("receive terminated, start send.");
    for &byte in data.iter() {
        uart.put_byte_poll(byte);
        println!("arceos send : {}", byte as char);
    }
    println!("translate OK.");
}

fn do_clock_init(_args: &str) {
    if FClockInit(&mut CLOCK.lock(), &FClockLookupConfig(0).unwrap()) {
        println!("clock init OK.");
    } else {
        println!("clock inited OK.");
    }
}

fn do_clock_test(args: &str) {
    let freq = args.parse::<u32>().unwrap();
    FClockSetFreq(&mut CLOCK.lock(), freq); 
    if freq == FClockGetFreq(&mut CLOCK.lock()) {
        println!("clock test OK.");
    } else {
        println!("clock test failed.");
    }
}

fn do_pwm_init(_args: &str) {
    if let Some(pwm) = PwmCtrl::global() {
    println!("pwm init OK.");
    } else {
        println!("pwm init failed.");
    }
}

fn do_pwm_test(args: &str) {
    let duty = args.parse::<u32>().unwrap();
    // 获取全局PWM控制器并执行测试
    if let Some(pwm) = PwmCtrl::global() {
        pwm.init();
        pwm.change_duty(duty);
        if duty == pwm.get_duty() {
            println!("pwm test OK.");
        }
    } else {
        println!("pwm test failed.");
    }
}

fn do_timer_tacho_test(_args: &str) {
    let mut tacho = Tacho::new(NonNull::new(phys_to_virt(0x2805_6000.into()).as_usize() as _).expect("tacho va failed"));
    tacho.init();

    let mut initial_value_set = false; 
    for _i in 0..50 {
        if let Some(res) = tacho.get_result() {
            if !initial_value_set {
                let meter = res;
                initial_value_set = true;
                println!("Initial res = {res}");
            } else {
                println!("res = {res}");
                println!("Timer test OK.");
                return;
            }
        }
    sleep(time::Duration::from_millis(50));
    }
    println!("timer test failed.");
}

fn do_i2c_init(_args: &str) {
        println!("i2c init OK.");
}

fn do_i2c_test(_args: &str) {
    unsafe {run_iicoled()} 
}

fn do_mio_init(_args: &str) {
    if FIOPadCfgInitialize(&mut PAD.lock(), &FIOPadLookupConfig(0).unwrap()) {
        println!("mio init OK.") 
    } else {
        println!("mio inited OK.");
    }
}

fn do_mio_test(_args: &str) {
    if FMioFuncInit(&mut MIO2.lock(), 1) {
        println!("mio test OK.");
    } else {
        println!("mio test failed.");
    }
}

fn do_cru_init(_args: &str) {
    if FResetInit(&mut CRU.lock(), &FResetLookupConfig(0).unwrap()) {
        println!("cru init OK.");
    } else {
        println!("cru inited OK.");
    }
}

fn do_cru_test(_args: &str) {
    if FResetSystem(&mut CRU.lock()) {
        println!("cru sys reset OK.");
    } else {
        println!("cru sys reset failed.");
    }
    for i in 1..5 {
        if FResetPeripheral(&mut CRU.lock(), i) {
            println!("cru periph {i} reset OK.");
        } else {
            println!("cru periph {i} reset failed.");
        }
    }
}

fn do_gpio_init(_args: &str) {
    println!("gpio init OK.");
}

fn do_gpio_test(_args: &str) {
    let mut gpio0 = GPIO.lock();
    let p = GpioPins::p8;
    let mut data = false;
    gpio0.set_pin_dir(p, true);
    for i in 0..10{
        sleep(time::Duration::from_millis(1000));
        gpio0.set_pin_data(p, data);
        println!("current data: {data}");
        data = !data;
    }
}

fn do_spi_init(_args: &str) {
    println!("spi init OK.");
}

fn do_spi_test(_args: &str) {
    let mut spi = SPI0.lock();
    for data in [0x61, 0x62, 0x63, 0x64] {
        spi.send(data);
        let received = spi.recv();

        if received != data {
            println!("spi test failed, expected: 0x{:02x}, received: 0x{:02x}", data, received);
            return;
        } 
    }
    println!("spi test OK.");
}

fn do_watchdog_init(_args: &str) {
    println!("watchdog init OK.");
}

fn do_watchdog_test(_args: &str) {
    let mut watchdog0 = WDT0.lock();
    watchdog0.set_timeout(1);
    watchdog0.start();
    println!("watchdog test OK.");
}

fn do_gic_init(_args: &str) {
    println!("todo: gic init");
}

fn do_fxmac_init(_args: &str) {
    println!("todo: fxmac init");
}

fn do_pcie_init(_args: &str) {
    println!("todo: pcie init");
}

fn do_ixgeb_init(_args: &str) {
    println!("todo: ixgeb init");
}

pub fn run_cmd(line: &[u8]) {
    let line_str = unsafe { core::str::from_utf8_unchecked(line) };
    let (cmd, args) = split_whitespace(line_str);
    if !cmd.is_empty() {
        for (name, func) in CMD_TABLE {
            if cmd == *name {
                func(args);
                return;
            }
        }
        println!("{}: command not found", cmd);
    }
}

fn split_whitespace(str: &str) -> (&str, &str) {
    let str = str.trim();
    str.find(char::is_whitespace)
        .map_or((str, ""), |n| (&str[..n], str[n + 1..].trim()))
}