import Cocoa
import FlutterMacOS

class MainFlutterWindow: NSWindow {
  override func awakeFromNib() {
    let flutterViewController = FlutterViewController()
    let windowFrame = self.frame
    self.contentViewController = flutterViewController
    self.setFrame(windowFrame, display: true)

    // Use a modern Pro Max portrait viewport (440 × 956 logical points), but
    // scale it down on shorter Mac displays so the window never feels taller
    // than the screen. The user can still resize either axis independently.
    let phoneViewport = NSSize(width: 440, height: 956)
    let availableHeight = self.screen?.visibleFrame.height ?? phoneViewport.height
    let scale = min(1.0, (availableHeight * 0.86) / phoneViewport.height)
    let defaultSize = NSSize(
      width: round(phoneViewport.width * scale),
      height: round(phoneViewport.height * scale)
    )

    self.contentResizeIncrements = NSSize(width: 1, height: 1)
    self.contentMinSize = NSSize(width: 340, height: 600)
    self.setContentSize(defaultSize)
    self.center()

    RegisterGeneratedPlugins(registry: flutterViewController)

    super.awakeFromNib()
  }
}
