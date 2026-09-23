import Cocoa
import FlutterMacOS

class MainFlutterWindow: NSWindow {
  override func awakeFromNib() {
    let flutterViewController = FlutterViewController()
    let windowFrame = self.frame
    self.contentViewController = flutterViewController
    self.setFrame(windowFrame, display: true)

    let phoneAspectRatio = NSSize(width: 1080, height: 2400)
    self.contentAspectRatio = phoneAspectRatio

    let defaultSize = NSSize(width: 405, height: 900)
    self.setContentSize(defaultSize)
    self.minSize = NSSize(width: 360, height: 800)

    RegisterGeneratedPlugins(registry: flutterViewController)

    super.awakeFromNib()
  }
}
