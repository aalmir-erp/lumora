package ae.servia.wear;

import android.app.Activity;
import android.os.Bundle;
import android.view.Gravity;
import android.widget.LinearLayout;
import android.widget.TextView;

/** Quote screen — placeholder for v1.24.0; full quote UI in v1.25. */
public class QuoteActivity extends Activity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setGravity(Gravity.CENTER);
        root.setBackgroundColor(0xFF312E81);
        root.setPadding(20, 20, 20, 20);

        TextView t = new TextView(this);
        t.setText("💬 QUOTE\n\nTypical UAE prices:\n· Deep clean 1BR: AED 450\n· AC service: AED 75/unit\n· Handyman visit: AED 100\n· Maid 4 hrs: AED 100");
        t.setTextColor(0xFFFFFFFF);
        t.setTextSize(11);
        t.setGravity(Gravity.CENTER);
        root.addView(t);

        setContentView(root);
    }
}
