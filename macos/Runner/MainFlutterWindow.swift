import Cocoa
import FlutterMacOS

class MainFlutterWindow: NSWindow {
  override func awakeFromNib() {
    let flutterViewController = FlutterViewController()
    let windowFrame = self.frame
    self.contentViewController = flutterViewController
    self.setFrame(windowFrame, display: true)

    let phoneAspectRatio = NSSize(width: 9, height: 19.5)
    self.contentAspectRatio = phoneAspectRatio

    let defaultSize = NSSize(width: 420, height: 910)
    self.setContentSize(defaultSize)
    self.minSize = NSSize(width: 360, height: 780)

    RegisterGeneratedPlugins(registry: flutterViewController)

    super.awakeFromNib()
  }
}
