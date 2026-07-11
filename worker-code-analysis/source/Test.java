import java.util.*;
import java.math.BigDecimal;

public class Test {

    private Date creationDate;

    public Test(Date date) {
        this.creationDate = date;
    }

    public Date getCreationDate() {
        return this.creationDate;
    }

    public void triggerViolations() {
        // PMD / SpotBugs: Constructing BigDecimal from double
        BigDecimal bd = new BigDecimal(0.1);

        // SpotBugs: Possible null pointer dereference
        String data = null;
        if (data == null) {
            System.out.println(data.length());
        }

        // Checkstyle: Bad local variable name & style issues
        int local_var_with_bad_name = 10;
	// Line contains tab character above

        // Indentation violation
      System.out.println("Indentation error");
    }
}