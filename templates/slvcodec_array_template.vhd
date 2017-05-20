  function to_slv (constant data: {{type}}) return std_logic_vector is
    constant W: natural := {{subtype.identifier}}_width;
    constant N: natural := data'length;
    variable slv: std_logic_vector(N*W-1 downto 0);
  begin
    for ii in 0 to N-1 loop
      slv((ii+1)*W-1 downto ii*W) := to_slv(data(ii));
    end loop;
    return slv; 
  end function;

  function from_slv (constant slv: std_logic_vector) return {{type}} is
    constant W: natural := {{subtype.identifier}}_width;
    constant N: natural := slv'length/W;
    variable output: {{type}}(N-1 downto 0);
  begin
    for ii in 0 to N-1 loop
      output(ii) := from_slv(slv((ii+1)*W-1 downto ii*W));
    end loop;
    return output; 
  end function;
